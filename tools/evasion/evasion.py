"""
EDR/SIEM Detection Evasion Tools

This module provides tools for testing detection capabilities against:
- Wazuh
- Splunk
- Other EDR/SIEM solutions

Techniques include:
- Code obfuscation
- API resolution evasion
- Process injection (parent spoofing, hollowing)
- Callback-based shellcode execution
- Memory pattern obfuscation
- Suspicious API call sequences
"""

from tools.base import BaseTool


class EvasionTool(BaseTool):
    """
    EDR/SIEM Detection Evasion Knowledge Base
    
    Provides evasion technique recommendations for testing against Wazuh, Splunk, and other EDR/SIEM solutions.
    This is an advisory tool - recommendations should be executed manually or via C2 framework.
    """
    
    name = "evasion"
    description = "EDR/SIEM evasion knowledge base & recommendations (advisory only - manual/C2 execution required)"
    requires_confirmation = True  # Knowledge base generation
    
    def _run(self, **kwargs) -> dict:
        """
        Generate evasion technique recommendations (advisory only).
        
        This tool provides knowledge base information and recommendations for evasion techniques.
        Actual execution should be performed manually or via C2 framework (e.g., Sliver integration).
        
        Args:
            technique: The evasion technique to get recommendations for
                - obfuscate_code: Code obfuscation techniques for payload delivery
                - api_resolution: Dynamic API resolution strategies
                - process_injection: Process injection recommendations
                - callback_execution: Callback-based execution methods
                - memory_obfuscation: Memory obfuscation techniques
                - api_sequence: Behavioral API patterns to test
            target_edr: Target EDR/SIEM (wazuh, splunk, sentinel, etc.)
            payload_path: Optional - path reference for documentation
        
        Returns:
            Dictionary with technique recommendations, tools, and execution guidance
        """
        
        technique = kwargs.get("technique", "info")
        target_edr = kwargs.get("target_edr", "wazuh")
        payload_path = kwargs.get("payload_path", "")
        
        if technique == "info":
            return self._get_techniques_info()
        
        elif technique == "obfuscate_code":
            return self._obfuscate_code(target_edr, payload_path)
        
        elif technique == "api_resolution":
            return self._api_resolution_evasion(target_edr)
        
        elif technique == "process_injection":
            return self._process_injection(target_edr, kwargs.get("injection_type", "parent_spoofing"))
        
        elif technique == "callback_execution":
            return self._callback_execution(target_edr)
        
        elif technique == "memory_obfuscation":
            return self._memory_obfuscation(target_edr)
        
        elif technique == "api_sequence":
            return self._suspicious_api_sequence(target_edr)
        
        else:
            return self._error(f"Unknown evasion technique: {technique}")
    
    def _get_techniques_info(self) -> dict:
        """Return information about available evasion techniques."""
        techniques = {
            "obfuscate_code": {
                "description": "Obfuscate shellcode/payload to evade signature detection",
                "tools_used": ["Shikata Ga Nai", "Python obfuscators", "Custom encoders"],
                "targets": ["Wazuh", "Splunk", "Microsoft Defender"],
                "effectiveness": "High against signature-based detection"
            },
            "api_resolution": {
                "description": "Dynamic API resolution using GetProcAddress to evade static analysis",
                "tools_used": ["GetProcAddress", "LoadLibrary", "Runtime resolvers"],
                "targets": ["Wazuh", "Splunk", "EDR agents"],
                "effectiveness": "Bypasses static import detection"
            },
            "process_injection": {
                "description": "Process injection via parent spoofing or process hollowing",
                "tools_used": ["Mimikatz", "Empire", "Invoke-ProcessInjection"],
                "injection_types": ["parent_spoofing", "process_hollowing", "dll_injection"],
                "targets": ["Wazuh", "Splunk", "Windows Defender"],
                "effectiveness": "Evades direct process detection"
            },
            "callback_execution": {
                "description": "Execute malicious code in callback functions (WinEventHook, SetTimer, etc.)",
                "tools_used": ["SetWindowsHookEx", "SetTimer", "RegisterPower NotificationHandler"],
                "targets": ["Behavioral EDR", "Wazuh", "Splunk"],
                "effectiveness": "Hides direct code execution"
            },
            "memory_obfuscation": {
                "description": "Obfuscate memory patterns and allocations to evade memory scanning",
                "tools_used": ["VirtualAllocExNuma", "Custom allocators", "Memory encryption"],
                "targets": ["EDR memory scanners"],
                "effectiveness": "Bypasses memory signature detection"
            },
            "api_sequence": {
                "description": "Execute suspicious API call sequences to test behavioral detection",
                "tools_used": ["Custom code", "Mimikatz", "Empire"],
                "api_patterns": [
                    "OpenProcess → ReadProcessMemory → WriteProcessMemory",
                    "CreateRemoteThread → WaitForSingleObject",
                    "CreateProcessWithTokenW (token theft)",
                    "RegOpenKeyEx → RegQueryValueEx → RegSetValueEx (registry tampering)"
                ],
                "targets": ["Behavioral EDR", "Wazuh"],
                "effectiveness": "Tests behavioral detection accuracy"
            }
        }
        
        return {
            "success": True,
            "techniques": techniques,
            "message": "EDR/SIEM evasion techniques available",
            "recommendation": "Use against Wazuh, Splunk, Microsoft Sentinel, and other EDR/SIEM solutions"
        }
    
    def _obfuscate_code(self, target_edr: str, payload_path: str) -> dict:
        """Obfuscate code/shellcode for evasion."""
        return {
            "success": True,
            "technique": "code_obfuscation",
            "target_edr": target_edr,
            "methods_applied": [
                "Shikata Ga Nai encoding (polymorphic XOR)",
                "Dead code insertion",
                "Control flow flattening",
                "Function call indirection",
                "Register preservation obfuscation"
            ],
            "evasion_factors": [
                "Avoids signature detection (signatures look for specific patterns)",
                "Polymorphic - changes with each execution",
                "Anti-disassembly techniques applied",
                "String obfuscation to hide API names"
            ],
            "detection_bypass": f"Obfuscated payload evades {target_edr} signature-based detection",
            "payload_hash_original": "N/A" if not payload_path else f"Original: <hash>",
            "payload_hash_obfuscated": "Different each run",
            "status": "Ready for deployment"
        }
    
    def _api_resolution_evasion(self, target_edr: str) -> dict:
        """Dynamic API resolution to evade static detection."""
        return {
            "success": True,
            "technique": "dynamic_api_resolution",
            "target_edr": target_edr,
            "methods": [
                "GetProcAddress for dynamic function resolution",
                "LoadLibrary for dynamic DLL loading",
                "Hashing to obfuscate API names"
            ],
            "bypassed_detections": [
                "Static import table scanning",
                "IAT hooking detection",
                "Direct API call interception"
            ],
            "evasion_benefit": "No suspicious imports in PE header - looks clean to static analysis",
            "runtime_resolution": "APIs resolved at runtime, not compile-time",
            "splunk_evasion": "Splunk queries for specific DLL imports won't detect dynamic loads",
            "wazuh_evasion": "Wazuh behavioral patterns may catch this, but signature detection bypassed"
        }
    
    def _process_injection(self, target_edr: str, injection_type: str) -> dict:
        """Process injection techniques."""
        techniques_info = {
            "parent_spoofing": {
                "description": "Spoof parent process to appear as trusted process",
                "trusted_parents": ["svchost.exe", "explorer.exe", "system.exe"],
                "wazuh_bypass": "Wazuh may not flag process with trusted parent",
                "detection_point": "Check actual parent in memory, not ppid"
            },
            "process_hollowing": {
                "description": "Hollow out legitimate process and inject malicious code",
                "legitimate_processes": ["notepad.exe", "calc.exe", "msiexec.exe"],
                "memory_operations": ["VirtualAllocEx", "WriteProcessMemory", "SetThreadContext"],
                "splunk_evasion": "Process appears legitimate to Splunk if not monitoring memory writes",
                "detection_point": "Memory inconsistency between PE header and actual memory"
            },
            "dll_injection": {
                "description": "Inject malicious DLL into legitimate process",
                "injection_methods": ["CreateRemoteThread + LoadLibraryA", "SetWindowsHookEx"],
                "evasion_benefit": "Runs under legitimate process context",
                "detection_point": "Unsigned DLL in legitimate process directory"
            }
        }
        
        info = techniques_info.get(injection_type, techniques_info["parent_spoofing"])
        
        return {
            "success": True,
            "technique": "process_injection",
            "injection_type": injection_type,
            "target_edr": target_edr,
            "details": info,
            "api_calls_used": [
                "OpenProcess (PROCESS_ALL_ACCESS)",
                "VirtualAllocEx",
                "WriteProcessMemory",
                "CreateRemoteThread" if injection_type != "parent_spoofing" else "CreateProcessWithTokenW"
            ],
            "status": "Injection technique ready"
        }
    
    def _callback_execution(self, target_edr: str) -> dict:
        """Execute code via callback mechanisms."""
        return {
            "success": True,
            "technique": "callback_based_execution",
            "target_edr": target_edr,
            "callback_mechanisms": [
                "SetWindowsHookEx - Keyboard/mouse hook callbacks",
                "SetTimer - Timer callbacks",
                "EnumSystemLocales - Callback enumeration",
                "RegisterPowerSettingNotification - Power events",
                "WMI Event consumers - WMI callbacks"
            ],
            "execution_flow": [
                "1. Register callback function",
                "2. Trigger event (keystroke, timer, power change, etc.)",
                "3. Callback executes malicious code",
                "4. Appears as system event, not direct execution"
            ],
            "wazuh_bypass": "Wazuh may not correlate callback events to malicious code",
            "splunk_evasion": "Callbacks appear as normal system events in logs",
            "behavioral_detection_risk": "Modern behavioral EDR may detect unusual patterns",
            "most_evasive": "SetWindowsHookEx with legitimate-looking trigger events"
        }
    
    def _memory_obfuscation(self, target_edr: str) -> dict:
        """Obfuscate memory patterns."""
        return {
            "success": True,
            "technique": "memory_obfuscation",
            "target_edr": target_edr,
            "methods": [
                "VirtualAllocExNuma - Allocate from non-standard NUMA nodes",
                "Encrypt memory pages at rest",
                "Allocate in non-contiguous regions",
                "Mimicry of legitimate process memory layout",
                "Delay-load shellcode from disk"
            ],
            "signature_evasion": "Breaks known shellcode signatures in memory",
            "detection_bypass": [
                "Yara rules for known shellcode patterns evaded",
                "Memory scanners see encrypted data",
                "Non-standard allocation patterns confuse heuristics"
            ],
            "wazuh_memory_scanning": "Wazuh memory scanning bypassed by encryption",
            "runtime_decryption": "Only decrypted when about to execute (XOR, AES, custom)",
            "decryption_pattern": "Minimal window for detection during decryption"
        }
    
    def _suspicious_api_sequence(self, target_edr: str) -> dict:
        """Test behavioral detection with suspicious API sequences."""
        return {
            "success": True,
            "technique": "behavioral_api_sequence_test",
            "target_edr": target_edr,
            "api_sequences": [
                {
                    "name": "Credential Theft",
                    "sequence": ["OpenProcess", "ReadProcessMemory", "WriteProcessMemory"],
                    "targets": "lsass.exe process",
                    "tools": "Mimikatz-style credential dump"
                },
                {
                    "name": "Code Injection",
                    "sequence": ["OpenProcess (PROCESS_ALL_ACCESS)", "VirtualAllocEx", "WriteProcessMemory", "CreateRemoteThread"],
                    "targets": "Legitimate process (notepad, explorer)",
                    "tools": "Empire, Cobalt Strike"
                },
                {
                    "name": "Token Impersonation",
                    "sequence": ["OpenProcessToken", "DuplicateToken", "SetThreadToken", "CreateProcessWithTokenW"],
                    "privilege_escalation": True,
                    "tools": "Mimikatz, PowerShell Empire"
                },
                {
                    "name": "Registry Tampering",
                    "sequence": ["RegOpenKeyEx", "RegQueryValueEx", "RegSetValueEx", "RegCloseKey"],
                    "targets": ["HKLM\\Software\\...", "HKEY_CURRENT_USER\\..."],
                    "persistence": "Run keys, shell override",
                    "tools": "Custom scripts, Mimikatz"
                },
                {
                    "name": "Service Creation",
                    "sequence": ["OpenSCManager", "CreateService", "StartService"],
                    "service_name": "Suspicious or mimicking legitimate service",
                    "tools": "PsExec, Empire"
                }
            ],
            "detection_effectiveness": {
                "signature_based": "Not detected - APIs are legitimate",
                "behavioral": "Should be detected if correlation is good",
                "heuristic": "Depends on EDR sensitivity"
            },
            "wazuh_expected": "Should trigger behavioral rules if configured",
            "splunk_expected": "Should correlate API sequences if dashboards configured",
            "evasion_tip": "Execute sequences quickly; slow execution may not trigger detection"
        }
    
    def _error(self, message: str, **kwargs) -> dict:
        """Return error response."""
        return {
            "success": False,
            "error": message,
            **kwargs
        }
