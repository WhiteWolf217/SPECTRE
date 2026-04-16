import json
import re
from agent.llm import OllamaClient
from agent.prompts import PLANNER_SYSTEM


class Planner:
    """
    Takes an engagement goal + target and produces a structured
    ATT&CK-mapped attack plan using the LLM.

    The plan is used by the agent core to guide its reasoning
    about what to do next.
    """

    def __init__(self, llm: OllamaClient):
        self.llm = llm

    def plan(self, goal: str, target: str, engagement_type: str = "external", context: str = "") -> dict:
        """
        Generate an attack plan for the given goal and target.

        Args:
            goal: User's objective
            target: Target IP or domain
            engagement_type: external | internal | web | ad
            context: Optional context from reconnaissance (e.g., open ports found)

        Returns a dict with phases, each containing:
        - phase name
        - MITRE TTP
        - description
        - suggested tools
        - dependency on previous phase
        """
        context_info = f"\nReconnaissance findings:\n{context}" if context else ""
        
        prompt = (
            f"Generate an attack plan for this engagement:\n"
            f"Goal: {goal}\n"
            f"Target: {target}\n"
            f"Type: {engagement_type}\n"
            f"{context_info}\n\n"
            f"Output ONLY valid JSON. No markdown. No explanation."
        )

        try:
            response = self.llm.chat(
                messages=[{"role": "user", "content": prompt}],
                system=PLANNER_SYSTEM,
                temperature=0.1,  # very deterministic for planning
            )

            # Strip markdown code fences if LLM wraps in them
            clean = re.sub(r"```(?:json)?", "", response).strip().strip("`").strip()

            plan = json.loads(clean)
            return plan

        except json.JSONDecodeError:
            # LLM didn't return valid JSON — return a safe fallback plan
            return self._fallback_plan(goal, target, engagement_type)
        except Exception as e:
            return self._fallback_plan(goal, target, engagement_type)

    def _fallback_plan(self, goal: str, target: str, engagement_type: str) -> dict:
        """
        Default plan used when LLM fails to produce valid JSON.
        Covers the standard recon → enum → exploit flow.
        """
        is_ad = engagement_type in ("ad", "internal")

        phases = [
            {
                "phase":       "Reconnaissance",
                "ttp":         "T1595",
                "description": "Port scan and service fingerprinting",
                "tools":       ["nmap"],
                "depends_on":  None,
            },
            {
                "phase":       "Service Enumeration",
                "ttp":         "T1046",
                "description": "Enumerate detected services based on nmap results",
                "tools":       ["nuclei", "whatweb", "ffuf"],
                "depends_on":  "Reconnaissance",
            },
            {
                "phase":       "CVE Analysis",
                "ttp":         "T1190",
                "description": "Search for CVEs affecting detected service versions",
                "tools":       ["cve-autoscan"],
                "depends_on":  "Reconnaissance",
            },
        ]

        if is_ad:
            phases += [
                {
                    "phase":       "AD Enumeration",
                    "ttp":         "T1087",
                    "description": "Enumerate Active Directory users, groups, and policies",
                    "tools":       ["crackmapexec", "ldapdomaindump", "bloodhound"],
                    "depends_on":  "Reconnaissance",
                },
                {
                    "phase":       "Kerberos Attacks",
                    "ttp":         "T1558",
                    "description": "Kerberoasting and AS-REP roasting attempts",
                    "tools":       ["kerbrute", "impacket"],
                    "depends_on":  "AD Enumeration",
                },
                {
                    "phase":       "Credential Access",
                    "ttp":         "T1003",
                    "description": "Dump credentials if access obtained",
                    "tools":       ["impacket", "crackmapexec"],
                    "depends_on":  "Kerberos Attacks",
                },
            ]
        else:
            phases += [
                {
                    "phase":       "Web Application Testing",
                    "ttp":         "T1190",
                    "description": "Test for web vulnerabilities",
                    "tools":       ["sqlmap", "dalfox", "nikto", "feroxbuster"],
                    "depends_on":  "Service Enumeration",
                },
                {
                    "phase":       "Credential Brute Force",
                    "ttp":         "T1110",
                    "description": "Brute force credentials on exposed services",
                    "tools":       ["hydra"],
                    "depends_on":  "Service Enumeration",
                },
            ]

        return {
            "goal":            goal,
            "target":          target,
            "engagement_type": engagement_type,
            "phases":          phases,
        }

    def format_plan(self, plan: dict) -> str:
        """Format plan as readable text for display."""
        lines = [
            f"Attack Plan — {plan.get('goal', 'N/A')}",
            f"Target: {plan.get('target', 'N/A')}",
            f"Type:   {plan.get('engagement_type', 'N/A')}",
            "",
        ]
        for i, phase in enumerate(plan.get("phases", []), 1):
            lines.append(
                f"  {i}. [{phase['ttp']}] {phase['phase']}"
                f"\n     Tools: {', '.join(phase['tools'])}"
                f"\n     {phase['description']}"
            )
        return "\n".join(lines)
