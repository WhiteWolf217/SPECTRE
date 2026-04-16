import json
import re
from typing import Optional, Callable

from agent.llm import OllamaClient
from agent.memory import AgentMemory
from agent.planner import Planner
from agent.prompts import (
    AGENT_SYSTEM,
    build_context_prompt,
    build_tool_result_prompt,
    build_dispatch_prompt,
)
from core.executor import Executor
from core.parser import Parser
from db.store import Store


class AgentCore:
    """
    SPECTRE ReAct Agent.

    Think → Act → Observe → Think → ...

    Every tool call is presented to the operator for confirmation
    before execution. The agent loop continues until:
    - The goal is marked DONE by the LLM
    - The operator types 'stop'
    - Max iterations reached
    """

    MAX_ITERATIONS = 20

    def __init__(
        self,
        store: Store,
        engagement_id: int,
        on_thought:    Optional[Callable] = None,
        on_tool_call:  Optional[Callable] = None,
        on_finding:    Optional[Callable] = None,
        on_done:       Optional[Callable] = None,
    ):
        self.store         = store
        self.engagement_id = engagement_id
        self.llm           = OllamaClient()
        self.planner       = Planner(self.llm)
        self.executor      = Executor(db_store=store, engagement_id=engagement_id)

        # Callbacks — used by the UI to display output
        # If None, falls back to print()
        self.on_thought   = on_thought   or (lambda msg: print(f"THOUGHT: {msg}"))
        self.on_tool_call = on_tool_call or (lambda tc: print(f"TOOL: {tc}"))
        self.on_finding   = on_finding   or (lambda f: print(f"FINDING: {f}"))
        self.on_done      = on_done      or (lambda msg: print(f"DONE: {msg}"))

        # Import tools registry from CLI
        self._tools = self._load_tools()

    def _load_tools(self) -> dict:
        """Import the tool registry."""
        from tools.recon.nmap import Nmap
        from tools.recon.recon import Subfinder, Amass, WhatWeb, TheHarvester, Whois
        from tools.web.web import Nuclei, Ffuf, Sqlmap, Nikto, Dalfox, Feroxbuster
        from tools.ad.ad import (CrackMapExec, BloodHound, Impacket,
                                  Kerbrute, Certipy, LdapDomainDump)
        from tools.bruteforce.bruteforce import Hydra, Hashcat, John
        from tools.exploit.cve import CVESearch, CVEAutoScan
        from tools.evasion.evasion import EvasionTool

        return {
            "nmap": Nmap(), "subfinder": Subfinder(), "amass": Amass(),
            "whatweb": WhatWeb(), "theharvester": TheHarvester(), "whois": Whois(),
            "nuclei": Nuclei(), "ffuf": Ffuf(), "sqlmap": Sqlmap(),
            "nikto": Nikto(), "dalfox": Dalfox(), "feroxbuster": Feroxbuster(),
            "crackmapexec": CrackMapExec(), "bloodhound": BloodHound(),
            "impacket": Impacket(), "kerbrute": Kerbrute(),
            "certipy": Certipy(), "ldapdomaindump": LdapDomainDump(),
            "hydra": Hydra(), "hashcat": Hashcat(), "john": John(),
            "cve-search": CVESearch(), "cve-autoscan": CVEAutoScan(),
            "evasion": EvasionTool(),
        }

    def run(
        self,
        goal: str,
        confirm_fn: Callable,
    ) -> AgentMemory:
        """
        Main agent loop with adaptive planning.

        1. Run initial reconnaissance (nmap, etc.)
        2. Analyze findings
        3. Generate context-aware attack plan
        4. Ask operator which attacks to perform
        5. Execute selected attacks

        Args:
            goal:       What the operator wants to achieve
            confirm_fn: Callable(tool_name, args) → bool
                        Called before every tool execution.

        Returns:
            AgentMemory with everything discovered
        """
        eng = self.store.get_engagement(self.engagement_id)
        if not eng:
            raise ValueError(f"Engagement {self.engagement_id} not found")

        target          = eng["target"]
        engagement_type = eng["type"]

        # Initialise memory
        memory = AgentMemory(
            target=target,
            goal=goal,
            engagement_type=engagement_type,
        )

        # PHASE 1: Initial Reconnaissance
        self.on_thought("Phase 1: Running initial reconnaissance...")
        memory.add_note("Starting reconnaissance phase")
        
        # Run nmap automatically on IP targets
        if self._is_ip(target):
            self.on_thought("Detected IP address. Running nmap port scan...")
            nmap_tool = self._tools.get("nmap")
            if nmap_tool:
                # Select flags based on engagement type
                flags = self._get_nmap_flags(engagement_type)
                self.on_thought(f"Using nmap flags: {flags}")
                
                # Run nmap without waiting for confirmation
                result = self.executor.run(nmap_tool, target=target, flags=flags, save=True)
                memory.add_tool_run("nmap", {"target": target, "flags": flags}, result)
                
                # Parse and extract open ports
                if result.get("success"):
                    parsed_nmap = Parser.nmap(result.get("stdout", ""))
                    ports_info = []
                    for host in parsed_nmap.get("hosts", []):
                        for port in host.get("open_ports", []):
                            port_num = port.get("port", "?")
                            service = port.get("service", "unknown")
                            ports_info.append((port_num, service))
                            memory.add_open_ports([port_num])
                    
                    if ports_info:
                        memory.add_note(f"Open ports found: {ports_info}")
                        ports_summary = "\n".join([f"  - {p}: {s}" for p, s in ports_info])
                        self.on_thought(f"Found open ports:\n{ports_summary}")
                else:
                    self.on_thought(f"Nmap scan failed or timed out. Error: {result.get('stderr', 'unknown')}")

        # PHASE 2: Generate context-aware plan based on findings
        self.on_thought("\nPhase 2: Generating attack plan based on findings...")
        context_summary = memory.summary()
        
        plan = self.planner.plan(goal, target, engagement_type, context=context_summary)
        plan_text = self.planner.format_plan(plan)
        self.on_thought(f"\n{plan_text}")
        memory.add_note(f"Context-aware attack plan generated: {len(plan.get('phases', []))} phases")

        # PHASE 3: Ask operator which attacks to execute
        self.on_thought("\n" + "="*60)
        self.on_thought("Which attacks would you like to perform?")
        self.on_thought("Examples: 'run hydra on ssh', 'scan for web vulns', 'test all services'")
        self.on_thought("="*60)

        # Build initial context message for ReAct loop
        context = build_context_prompt(
            goal=goal,
            target=target,
            engagement_type=engagement_type,
            memory_summary=context_summary,
            available_tools=list(self._tools.keys()),
        )
        memory.add_user_message(context)

        # PHASE 4: ReAct loop for attack execution
        iteration = 0
        while iteration < self.MAX_ITERATIONS:
            iteration += 1

            # Get next action from LLM
            try:
                response = self.llm.chat(
                    messages=memory.get_messages(),
                    system=AGENT_SYSTEM,
                    temperature=0.2,
                )
            except RuntimeError as e:
                self.on_thought(f"LLM error: {e}")
                self.agent_running = False
                break

            memory.add_assistant_message(response)

            # Parse response
            parsed = self._parse_response(response)

            # ── THOUGHT ──────────────────────────────────────────────────────
            if parsed["type"] == "thought":
                self.on_thought(parsed["content"])
                # Feed thought back as user prompt to keep loop going
                memory.add_user_message("Continue. What's your next action?")

            # ── TOOL CALL ─────────────────────────────────────────────────────
            elif parsed["type"] == "tool_call":
                tc = parsed["content"]
                self.on_tool_call(tc)

                tool_name = tc.get("tool", "").lower()
                args      = tc.get("args", {})
                ttp       = tc.get("ttp", "")
                reason    = tc.get("reason", "")

                tool = self._tools.get(tool_name)
                if not tool:
                    result_msg = f"Unknown tool: {tool_name}. Choose from: {', '.join(self._tools.keys())}"
                    memory.add_user_message(f"ERROR: {result_msg}")
                    continue

                # Operator confirmation gate
                confirmed = confirm_fn(tool_name, args)
                if not confirmed:
                    memory.add_user_message(
                        f"Operator skipped {tool_name}. Choose a different approach."
                    )
                    continue

                # Execute tool
                result = self.executor.run(tool, save=True, **args)
                memory.add_tool_run(tool_name, args, result)

                # If nmap — extract open ports and update memory
                if tool_name == "nmap" and result.get("success"):
                    parsed_nmap = Parser.nmap(result.get("stdout", ""))
                    ports = []
                    for host in parsed_nmap.get("hosts", []):
                        ports += [p["port"] for p in host.get("open_ports", [])]
                    if ports:
                        memory.add_open_ports(ports)
                        memory.add_note(f"Open ports on {target}: {ports}")

                # Feed result back to LLM
                result_prompt = build_tool_result_prompt(tool_name, result)
                result_prompt += f"\nCurrent knowledge:\n{memory.summary()}"
                memory.add_user_message(result_prompt)

            # ── FINDING ───────────────────────────────────────────────────────
            elif parsed["type"] == "finding":
                f = parsed["content"]
                self.on_finding(f)

                # Save to memory
                memory.add_finding(
                    title=f.get("title", "Unknown"),
                    severity=f.get("severity", "info"),
                    description=f.get("description", ""),
                    ttp=f.get("ttp", ""),
                    host=f.get("host", target),
                    port=f.get("port"),
                    evidence=f.get("evidence", ""),
                )

                # Save to DB
                self.store.add_finding(
                    engagement_id=self.engagement_id,
                    title=f.get("title", "Unknown"),
                    description=f.get("description", ""),
                    severity=f.get("severity", "info"),
                    ttp=f.get("ttp", ""),
                    evidence=f.get("evidence", ""),
                    host=f.get("host", target),
                    port=f.get("port"),
                    tool="agent",
                )

                memory.add_user_message(
                    f"Finding recorded: {f.get('title')}. Continue with next action."
                )

            # ── DONE ──────────────────────────────────────────────────────────
            elif parsed["type"] == "done":
                self.on_done(parsed["content"])
                break

            # ── UNKNOWN ───────────────────────────────────────────────────────
            else:
                # LLM produced something unexpected — nudge it
                memory.add_user_message(
                    "Output was not in the expected format. "
                    "Use THOUGHT:, <tool_call>, <finding>, or DONE: format."
                )

        return memory

    def _is_ip(self, target: str) -> bool:
        """Check if target is an IP address."""
        import re
        ip_pattern = r'^(\d{1,3}\.){3}\d{1,3}$'
        return bool(re.match(ip_pattern, target))
    
    def _get_nmap_flags(self, engagement_type: str) -> str:
        """
        Get optimized nmap flags based on engagement type.
        
        Args:
            engagement_type: external | internal | web | ad | edr
            
        Returns:
            Nmap flags string
        """
        # Flag explanations:
        # -A: Aggressive (includes -sV, -sC, OS detection, script scanning, traceroute)
        # -p-: Scan all 65535 ports
        # -T4: Timing template (fast)
        # -T3: Timing template (normal, safer for internal networks)
        # -vv: Very verbose (shows more details)
        
        if engagement_type == "external":
            # External: Comprehensive, -A already includes -sV and -sC
            return "-A -p- -T4 -vv"
        elif engagement_type == "internal":
            # Internal: Balanced, -A with slightly slower timing for stability
            return "-A -p- -T3"
        elif engagement_type == "web":
            # Web: Focus on common web ports, no need for -A
            return "-sV -sC -p 80,443,8080,8443,8000,8888,3000,5000 -T4"
        elif engagement_type == "ad":
            # AD: Focus on Windows services, no need for -A
            return "-sV -sC -p 135,139,445,3389,5985,5986,88,389,636,3306,1433 -T4"
        elif engagement_type == "edr":
            # EDR/SIEM Evasion: against Wazuh, Splunk, etc.
            return "-sV -sC -O -p- -T3"
        else:
            # Default: Standard comprehensive scan
            return "-A -T4"

    # ── Response parser ────────────────────────────────────────────────────────

    def _parse_response(self, response: str) -> dict:
        """
        Parse the LLM response into a typed action.

        Returns dict with:
            type: "thought" | "tool_call" | "finding" | "done" | "unknown"
            content: str | dict
        """
        response = response.strip()

        # Check for DONE
        if response.upper().startswith("DONE:"):
            return {"type": "done", "content": response[5:].strip()}

        # Check for THOUGHT
        if response.upper().startswith("THOUGHT:"):
            return {"type": "thought", "content": response[8:].strip()}

        # Check for tool_call JSON block
        tc_match = re.search(r"<tool_call>\s*(\{.*?\})\s*</tool_call>", response, re.DOTALL)
        if tc_match:
            try:
                tc = json.loads(tc_match.group(1))
                return {"type": "tool_call", "content": tc}
            except json.JSONDecodeError:
                pass

        # Check for finding JSON block
        f_match = re.search(r"<finding>\s*(\{.*?\})\s*</finding>", response, re.DOTALL)
        if f_match:
            try:
                f = json.loads(f_match.group(1))
                return {"type": "finding", "content": f}
            except json.JSONDecodeError:
                pass

        # Try bare JSON (LLM sometimes skips tags)
        try:
            data = json.loads(response)
            if "tool" in data:
                return {"type": "tool_call", "content": data}
            if "title" in data and "severity" in data:
                return {"type": "finding", "content": data}
        except json.JSONDecodeError:
            pass

        # Fallback — treat as thought
        if len(response) > 0:
            return {"type": "thought", "content": response}

        return {"type": "unknown", "content": response}
