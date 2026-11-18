from __future__ import annotations

import re

# 10 Enterprise IT Knowledge Base articles covering common workplace IT support domains
ARTICLES: list[dict] = [
    {
        "id": "KB0001",
        "title": "GlobalProtect VPN Troubleshooting & Authentication Failure",
        "category": "Network",
        "tags": ["vpn", "globalprotect", "network", "authentication", "error 809", "pangps"],
        "owner": "Network Engineering",
        "status": "published",
        "updated": "2026-11-10",
        "symptoms": "User cannot connect to corporate VPN. PanGPS service reports error 809 or authentication keeps failing after password change.",
        "steps": [
            "Verify network connectivity by pinging internal gateway or browsing an external HTTPS site.",
            "Confirm that your corporate password was not recently updated; if updated, stored VPN credentials must be refreshed.",
            "Open GlobalProtect client -> Settings -> General -> Sign Out to clear cached credentials.",
            "Restart the PanGPS Windows service using services.msc or command: Restart-Service PanGPS.",
            "Launch GlobalProtect, enter vpn.northline.com as the portal address, and sign in with updated Entra ID credentials and MFA prompt.",
            "If error 809 persists, check local Windows Firewall rules for UDP ports 500 and 4500."
        ],
        "content": (
            "Title: GlobalProtect VPN Troubleshooting & Authentication Failure\n"
            "Article ID: KB0001 | Category: Network / VPN\n"
            "Summary: Guide to resolving GlobalProtect VPN connection and authentication failures.\n\n"
            "1. Symptoms & Root Causes:\n"
            "Users commonly experience connection failures when their enterprise directory password expires or is updated, "
            "leaving stale credential tokens in the PanGPS daemon cache. Symptoms include error 809 (gateway unreachable or "
            "handshake failed) and repeated authentication failure prompts.\n\n"
            "2. Step-by-Step Resolution:\n"
            "Step 1: Check your local internet connection and ensure external HTTPS traffic is functional.\n"
            "Step 2: If you recently changed your Windows / Entra ID password, log out of GlobalProtect to clear the stored hash.\n"
            "Step 3: In GlobalProtect, click the menu icon -> Settings -> General -> Sign Out.\n"
            "Step 4: Restart the PanGPS background service via Windows Services or run 'Restart-Service PanGPS'.\n"
            "Step 5: Connect to the primary gateway vpn.northline.com and complete the Multi-Factor Authentication challenge.\n"
            "Step 6: If connection remains blocked, verify corporate firewall rules allow UDP 500/4500 and IPsec encapsulation."
        ),
    },
    {
        "id": "KB0002",
        "title": "Password Expiration & Self-Service Entra ID Reset",
        "category": "Identity",
        "tags": ["password", "expired", "entra id", "active directory", "reset", "login", "identity"],
        "owner": "Identity Operations",
        "status": "published",
        "updated": "2026-11-08",
        "symptoms": "User password has expired, sign-in is rejected across all Microsoft 365 services and corporate laptop login.",
        "steps": [
            "Verify identity via alternate registered security method (SMS, Authenticator app, or manager approval channel).",
            "Access the Northline self-service password portal at https://identity.northline.com/reset.",
            "For automated self-healing, the helpdesk agent verifies the caller account is non-privileged and currently flagged as expired.",
            "Issue a temporary one-time password (OTP) delivered securely to the verified recovery phone or manager channel.",
            "User logs in with the OTP and is immediately prompted to create a new compliant password (minimum 14 characters, uppercase, lowercase, numbers, symbols).",
            "Allow 2 minutes for password synchronization across Entra ID, VPN, and on-prem domain controllers."
        ],
        "content": (
            "Title: Password Expiration & Self-Service Entra ID Reset\n"
            "Article ID: KB0002 | Category: Identity / Password\n"
            "Summary: Self-service and automated recovery procedures for expired enterprise passwords.\n\n"
            "1. Policy & Authorization:\n"
            "Enterprise security policy mandates password expiration every 90 days for standard accounts. "
            "When an account password expires, automated self-healing is permitted for standard non-privileged accounts. "
            "Privileged accounts (e.g., Domain Admins, Security Leads) require tier-2 manual identity verification.\n\n"
            "2. Resolution Workflow:\n"
            "Step 1: The self-heal agent or employee navigates to https://identity.northline.com/reset.\n"
            "Step 2: Diagnose account status in Microsoft Entra ID. Confirm the account is enabled and the 'PasswordExpired' flag is True.\n"
            "Step 3: Execute automated temporary password generation. A secure one-time passcode is generated with 15-minute validity.\n"
            "Step 4: Revoke existing active refresh tokens to prevent session hijacking.\n"
            "Step 5: The user authenticates with the temporary password and creates a new password with at least 14 characters.\n"
            "Step 6: System validates successful directory bind and updates ServiceNow incident to Resolved."
        ),
    },
    {
        "id": "KB0003",
        "title": "Multi-Factor Authentication (MFA) & Microsoft Authenticator Setup",
        "category": "Identity",
        "tags": ["mfa", "authenticator", "2fa", "microsoft authenticator", "phone change", "identity"],
        "owner": "Identity Operations",
        "status": "published",
        "updated": "2026-11-05",
        "symptoms": "User replaced mobile device or Microsoft Authenticator push notifications are not received.",
        "steps": [
            "Confirm employee identity using manager confirmation or verified secondary email.",
            "Reset the existing Microsoft Authenticator registration method in Microsoft Entra ID admin center.",
            "Guide employee to install Microsoft Authenticator app from official iOS App Store or Google Play Store.",
            "Navigate to https://aka.ms/mfasetup on corporate laptop and scan the new QR code with the mobile app.",
            "Approve the test notification number match challenge to confirm active verification."
        ],
        "content": (
            "Title: Multi-Factor Authentication (MFA) & Microsoft Authenticator Setup\n"
            "Article ID: KB0003 | Category: Identity / MFA\n"
            "Summary: Managing, resetting, and re-enrolling Microsoft Authenticator for enterprise sign-in.\n\n"
            "1. When to Reset MFA:\n"
            "MFA method resets are appropriate when employees switch phones, lose access to their authenticator app, "
            "or experience desynchronized TOTP code generation. Self-service reset clears old phone registrations.\n\n"
            "2. Setup Procedure:\n"
            "Step 1: The self-heal system clears the stale device registration token from Entra ID.\n"
            "Step 2: Employee browses to https://aka.ms/mfasetup on their trusted laptop.\n"
            "Step 3: Open Microsoft Authenticator on mobile -> tap Add Account -> Work or School Account.\n"
            "Step 4: Scan the 2D barcode displayed on the browser monitor.\n"
            "Step 5: Complete the two-digit number matching challenge to validate registration."
        ),
    },
    {
        "id": "KB0004",
        "title": "Account Unlock & Sign-In Lockout Resolution",
        "category": "Identity",
        "tags": ["account lockout", "unlock", "locked", "too many attempts", "entra id", "identity"],
        "owner": "Identity Operations",
        "status": "published",
        "updated": "2026-11-04",
        "symptoms": "User account locked due to excessive failed sign-in attempts (threshold: 10 consecutive failures).",
        "steps": [
            "Query Entra ID and Active Directory for caller lockout status and bad password count.",
            "Identify the source device or IP address causing repeated failed authentication attempts.",
            "Verify caller identity and confirm no active malicious credential stuffing alerts.",
            "Execute automated account unlock command: Set-ADUser -Identity <user> -ResetPasswordAtNextLogon $false -LockedOut $false.",
            "Instruct user to disconnect any mobile email client holding a stale password before retrying."
        ],
        "content": (
            "Title: Account Unlock & Sign-In Lockout Resolution\n"
            "Article ID: KB0004 | Category: Identity / Account Unlock\n"
            "Summary: Automated and self-service procedures for clearing account lockouts.\n\n"
            "1. Policy Rules:\n"
            "Standard accounts lock out after 10 invalid password attempts within a 15-minute rolling window. "
            "Self-healing is permitted automatically if no suspicious geographic anomalies are detected.\n\n"
            "2. Resolution Steps:\n"
            "Step 1: Check Microsoft Entra ID sign-in audit logs to verify whether the source is a known company laptop or mobile device.\n"
            "Step 2: Check whether cached credentials on an iPhone/Android Mail app are repeatedly triggering lockout.\n"
            "Step 3: Clear the lockout flag on Entra ID directory service.\n"
            "Step 4: Wait 60 seconds for tenant-wide directory replication.\n"
            "Step 5: Have the employee attempt login from their workstation."
        ),
    },
    {
        "id": "KB0005",
        "title": "Outlook Synchronization & OST Cache Repair Runbook",
        "category": "Collaboration",
        "tags": ["outlook", "email", "synchronization", "ost", "exchange", "mailbox", "cache"],
        "owner": "Collaboration Support",
        "status": "published",
        "updated": "2026-11-12",
        "symptoms": "Outlook shows 'Disconnected' or 'Trying to connect', new emails do not appear, or Send/Receive reports 0x8004010F.",
        "steps": [
            "Test mailbox accessibility via Outlook on the Web (OWA) at https://outlook.office.com to rule out tenant outages.",
            "If OWA works normally, the issue is isolated to the local workstation's Offline Storage File (OST cache).",
            "Exit Microsoft Outlook completely (verify Outlook.exe is terminated in Task Manager).",
            "Navigate to %localappdata%\\Microsoft\\Outlook in File Explorer.",
            "Rename the corrupt .ost file to .ost.old (do not delete immediately).",
            "Relaunch Outlook; the application will automatically create a fresh OST file and re-sync mail items from Microsoft 365 Exchange Online."
        ],
        "content": (
            "Title: Outlook Synchronization & OST Cache Repair Runbook\n"
            "Article ID: KB0005 | Category: Collaboration / Outlook\n"
            "Summary: Diagnosing and resolving desktop Outlook synchronization and corrupted OST cache files.\n\n"
            "1. Problem Diagnosis:\n"
            "When desktop Microsoft Outlook fails to synchronize emails while webmail (OWA) works, the local "
            "Offline Outlook Data File (.ost) has suffered corruption or cache index divergence. Symptoms include "
            "'Disconnected' status in the bottom status bar and error 0x8004010F.\n\n"
            "2. Step-by-Step Fix:\n"
            "Step 1: Confirm server-side mailbox health by browsing to https://outlook.office.com.\n"
            "Step 2: Close Outlook completely. Ensure no background Outlook processes remain in Task Manager.\n"
            "Step 3: Press Win + R, type '%localappdata%\\Microsoft\\Outlook', and hit Enter.\n"
            "Step 4: Locate the user email .ost file and rename it to 'username.ost.bak'.\n"
            "Step 5: Start Outlook. Outlook will automatically generate a new OST container and stream your mailbox from Exchange Online.\n"
            "Step 6: Allow initial synchronization to finish while plugged into high-speed network."
        ),
    },
    {
        "id": "KB0006",
        "title": "Corporate Wi-Fi (802.1x) Connection & Certificate Renewal",
        "category": "Network",
        "tags": ["wifi", "wireless", "network", "802.1x", "certificate", "northline-corp"],
        "owner": "Network Engineering",
        "status": "published",
        "updated": "2026-11-02",
        "symptoms": "Laptop cannot connect to Northline-Corp Wi-Fi SSID, receives 'Can't connect to this network' or cert untrusted alert.",
        "steps": [
            "Verify device certificate validity in User Certificates (certmgr.msc) under Personal -> Certificates.",
            "If the Northline Root CA or machine cert is expired, connect temporarily to Northline-Guest SSID.",
            "Open company portal app and trigger device compliance sync to pull updated 802.1x certificate.",
            "In Windows Wi-Fi settings, select 'Northline-Corp', click 'Forget', then reconnect.",
            "Choose Certificate-based EAP-TLS authentication when prompted."
        ],
        "content": (
            "Title: Corporate Wi-Fi (802.1x) Connection & Certificate Renewal\n"
            "Article ID: KB0006 | Category: Network / Wi-Fi\n"
            "Summary: Troubleshooting enterprise 802.1x EAP-TLS Wi-Fi authentication issues on corporate laptops.\n\n"
            "1. Overview:\n"
            "Northline-Corp uses WPA3-Enterprise 802.1x with device client certificates issued by corporate PKI. "
            "Connection errors typically occur when device certificates expire or Wi-Fi profile configs become stale.\n\n"
            "2. Resolution Steps:\n"
            "Step 1: Check if the Northline device certificate has expired in certmgr.msc.\n"
            "Step 2: Connect to Northline-Guest or plug in an Ethernet cable.\n"
            "Step 3: Open Company Portal -> Device Details -> Sync to refresh security certificates.\n"
            "Step 4: Remove the saved Wi-Fi profile: netsh wlan delete profile name='Northline-Corp'.\n"
            "Step 5: Re-select Northline-Corp Wi-Fi and connect using the newly refreshed enterprise certificate."
        ),
    },
    {
        "id": "KB0007",
        "title": "Laptop Performance Optimization & Disk Temp Cleanup",
        "category": "End User Computing",
        "tags": ["performance", "disk", "storage", "laptop slow", "temp files", "cleanup"],
        "owner": "Desktop Engineering",
        "status": "published",
        "updated": "2026-11-09",
        "symptoms": "Laptop running slow, C: drive low disk space alert (< 10 GB free), high background CPU usage.",
        "steps": [
            "Check available storage on system drive C:. Enterprise baseline requires at least 15 GB free.",
            "Execute automated cleanup of Windows Temp (%windir%\\Temp) and User Temp (%temp%).",
            "Clear Delivery Optimization download cache and Windows Update leftover staging files.",
            "Enable Windows Storage Sense to automatically clean up temporary application files.",
            "Restart the laptop to terminate runaway memory leaks and reload clean drivers."
        ],
        "content": (
            "Title: Laptop Performance Optimization & Disk Temp Cleanup\n"
            "Article ID: KB0007 | Category: End User Computing / Performance\n"
            "Summary: Automated self-healing for low disk space and laptop performance degradation.\n\n"
            "1. Automated Disk Cleanup Safety Policy:\n"
            "Automated cleanup is safe to execute unattended because it purges only non-essential temporary directories: "
            "C:\\Windows\\Temp, %localappdata%\\Temp, and Delivery Optimization cache. User documents, desktop files, "
            "and browser settings are never touched.\n\n"
            "2. Step-by-Step Remediation:\n"
            "Step 1: Check drive C: capacity. If free space is below 15 GB, trigger automated disk maintenance.\n"
            "Step 2: Purge user temp files and Windows Update staging buffers.\n"
            "Step 3: Verify reclaimed space exceeds 10 GB.\n"
            "Step 4: Check Task Manager for rogue background processes consuming > 80% CPU.\n"
            "Step 5: Reboot the workstation to finalize cleanup."
        ),
    },
    {
        "id": "KB0008",
        "title": "Software Provisioning & Catalog Installation Policy",
        "category": "Software",
        "tags": ["software", "provisioning", "install", "catalog", "license", "vscode", "docker", "postman"],
        "owner": "IT Asset Management",
        "status": "published",
        "updated": "2026-11-14",
        "symptoms": "User requests installation of development tools, productivity applications, or licensed enterprise software.",
        "steps": [
            "Submit request through the Self-Service Portal or IT Service Catalog.",
            "System automatically checks requester department eligibility and contractor status.",
            "For standard approved software (e.g., Visual Studio Code, Slack, Zoom), provisioning is pre-approved and automated immediately.",
            "For licensed software (e.g., Docker Desktop, Figma, Postman Enterprise), manager or cost-center approval is requested.",
            "Upon approval, deployment agent pushes the silent installer via Microsoft Intune / Jamf Pro.",
            "Software is installed in %ProgramFiles% without requiring local administrator rights."
        ],
        "content": (
            "Title: Software Provisioning & Catalog Installation Policy\n"
            "Article ID: KB0008 | Category: Software / Catalog\n"
            "Summary: Enterprise software provisioning lifecycle, approval policies, and installation automation.\n\n"
            "1. Software Catalog & Approval Rules:\n"
            "Northline operates a self-service software catalog integrated with ServiceNow Service Requests. "
            "- Pre-approved standard software (Visual Studio Code, Slack, Zoom): Zero approval required. Automatically dispatched.\n"
            "- Tier-2 licensed software (Docker Desktop, Figma Pro, Postman Enterprise): Requires line-manager approval and license pool validation.\n"
            "- Contractor policy: Contractors are eligible only for role-essential tools explicitly authorized in their statement of work.\n\n"
            "2. Delivery Mechanism:\n"
            "Step 1: Employee requests software through portal chat or catalog UI.\n"
            "Step 2: AI intent detection categorizes request as Service Request and checks catalog eligibility.\n"
            "Step 3: ServiceNow REQ/RITM ticket is generated with user justification.\n"
            "Step 4: Automated Provisioning API dispatches the deployment package to Microsoft Intune.\n"
            "Step 5: Notification is dispatched to user when installation completes."
        ),
    },
    {
        "id": "KB0009",
        "title": "Follow-Me Badge Printing & Print Spooler Recovery",
        "category": "End User Computing",
        "tags": ["printer", "printing", "papercut", "badge", "spooler", "follow me"],
        "owner": "End User Computing",
        "status": "published",
        "updated": "2026-11-07",
        "symptoms": "Print jobs not releasing at badge reader MFP printers, jobs stuck in local Windows print queue.",
        "steps": [
            "Check PaperCut print server queue for pending held jobs associated with employee RFID badge ID.",
            "If jobs are stuck in 'Sending to Printer' state locally, clear the Windows Print Spooler.",
            "Stop the Spooler service: Stop-Service spooler.",
            "Delete temporary spool files in C:\\Windows\\System32\\spool\\PRINTERS\\*.",
            "Restart Spooler: Start-Service spooler.",
            "Resubmit print document to Northline-FollowMe-Print virtual printer queue and tap badge at MFP terminal."
        ],
        "content": (
            "Title: Follow-Me Badge Printing & Print Spooler Recovery\n"
            "Article ID: KB0009 | Category: End User Computing / Printing\n"
            "Summary: Resolving stuck print queues and PaperCut badge release issues.\n\n"
            "1. Architecture:\n"
            "Northline utilizes PaperCut MF follow-me printing. Documents printed to the virtual queue are held securely "
            "on the server until released by tapping an employee RFID security badge at any multi-function printer (MFP).\n\n"
            "2. Spooler Recovery Procedure:\n"
            "Step 1: Inspect local Windows print queue. If a print job shows 'Error - Printing', do not resubmit repeatedly.\n"
            "Step 2: Restart the local Windows Print Spooler service.\n"
            "Step 3: Clear any locked shadow files in C:\\Windows\\System32\\spool\\PRINTERS.\n"
            "Step 4: Re-send the print job to 'Northline-FollowMe'.\n"
            "Step 5: Tap badge on physical badge scanner on the printer panel to release."
        ),
    },
    {
        "id": "KB0010",
        "title": "Windows System Services & Agent Health Management",
        "category": "End User Computing",
        "tags": ["service", "restart", "agent", "windows service", "panGPS", "intune"],
        "owner": "Desktop Engineering",
        "status": "published",
        "updated": "2026-11-06",
        "symptoms": "Critical endpoint management agent (PanGPS, Intune Management Extension, CrowdStrike) in stopped or hung state.",
        "steps": [
            "Identify the target agent service name and verify it is part of the approved Northline baseline image.",
            "Query service operational state via PowerShell: Get-Service -Name <service>.",
            "Attempt controlled restart of the service and its registered dependent services.",
            "Validate endpoint health check URL or local IPC pipe.",
            "Log restart event to endpoint diagnostic telemetry and ServiceNow CI record."
        ],
        "content": (
            "Title: Windows System Services & Agent Health Management\n"
            "Article ID: KB0010 | Category: End User Computing / Services\n"
            "Summary: Safe remediation runbooks for stopped or degraded local system services.\n\n"
            "1. Policy & Authorization:\n"
            "Analyst approval is required prior to restarting non-standard services. Baseline services (e.g., PanGPS, "
            "Intune Management Extension) may be restarted via automated playbooks with analyst sign-off.\n\n"
            "2. Runbook Steps:\n"
            "Step 1: Check current service status in service control manager.\n"
            "Step 2: If service is hung in 'StopPending', safely recycle process ID.\n"
            "Step 3: Start the service and confirm status transitions to 'Running'.\n"
            "Step 4: Verify agent communicates with management portal."
        ),
    },
]

# Software Catalog definitions
CATALOG_ITEMS: list[dict] = [
    {
        "id": "vscode",
        "name": "Visual Studio Code",
        "owner": "Developer Tools",
        "license_type": "Free / Open Source",
        "licenses_total": None,
        "licenses_used": None,
        "approval": "none",
        "approval_reason": "Pre-approved standard developer editor for full-time Engineering and Product employees. Not issued to external contractors.",
        "provision_minutes": 1,
        "eligible": "Engineering and Product employees only. Contractors restricted.",
        "departments": ["Engineering", "Product"],
        "contractors_allowed": False,
        "summary": "Lightweight code editor with support for Python, JavaScript, TypeScript, Go, and extensions.",
        "aliases": ["vscode", "visual studio code", "vs code", "code editor", "visual studio"],
    },
    {
        "id": "docker",
        "name": "Docker Desktop",
        "owner": "Developer Tools",
        "license_type": "Subscription",
        "licenses_total": 100,
        "licenses_used": 76,
        "approval": "manager",
        "approval_reason": "Subscription required ($9/user/month). Auto-approved for Engineering; Manager approval required for other departments.",
        "provision_minutes": 3,
        "eligible": "Engineering, Data Science, and DevOps.",
        "departments": ["Engineering", "Data Science", "DevOps"],
        "contractors_allowed": True,
        "summary": "Container development environment for building, running, and managing Docker containers.",
        "aliases": ["docker", "docker desktop", "container"],
    },
    {
        "id": "postman",
        "name": "Postman Enterprise",
        "owner": "Developer Tools",
        "license_type": "Subscription",
        "licenses_total": 50,
        "licenses_used": 41,
        "approval": "manager",
        "approval_reason": "Dedicated API platform seat. Requires manager sign-off.",
        "provision_minutes": 2,
        "eligible": "Engineering and QA teams.",
        "departments": ["Engineering", "QA", "Product"],
        "contractors_allowed": True,
        "summary": "Complete API platform for building and testing REST and GraphQL endpoints.",
        "aliases": ["postman", "postman enterprise", "api client"],
    },
    {
        "id": "slack",
        "name": "Slack Enterprise Grid",
        "owner": "Collaboration Support",
        "license_type": "Enterprise Site",
        "licenses_total": 5000,
        "licenses_used": 3410,
        "approval": "none",
        "approval_reason": "Company-wide communication tool. Instantly provisioned.",
        "provision_minutes": 1,
        "eligible": "All employees and authorized contractors.",
        "departments": ["*"],
        "contractors_allowed": True,
        "summary": "Real-time enterprise team collaboration and messaging workspace.",
        "aliases": ["slack", "slack enterprise", "messaging"],
    },
    {
        "id": "figma",
        "name": "Figma Enterprise",
        "owner": "Design Systems",
        "license_type": "Subscription",
        "licenses_total": 30,
        "licenses_used": 28,
        "approval": "manager",
        "approval_reason": "Paid design seat ($45/month). Restricted to Design and UX roles.",
        "provision_minutes": 2,
        "eligible": "Design and Product UX teams only.",
        "departments": ["Design", "Product"],
        "contractors_allowed": False,
        "summary": "Collaborative interface design tool for UX/UI prototyping and design systems.",
        "aliases": ["figma", "figma enterprise", "ui design tool"],
    },
    {
        "id": "tableau",
        "name": "Tableau Desktop",
        "owner": "Business Intelligence",
        "license_type": "Subscription",
        "licenses_total": 25,
        "licenses_used": 22,
        "approval": "director",
        "approval_reason": "Cost-controlled BI tool ($70/month). Requires Director approval.",
        "provision_minutes": 5,
        "eligible": "Analytics, Finance, and Business Intelligence.",
        "departments": ["Analytics", "Finance", "Business Intelligence"],
        "contractors_allowed": False,
        "summary": "Data visualization and enterprise business intelligence platform.",
        "aliases": ["tableau", "tableau desktop", "bi tool"],
    },
]


def chunk_articles(articles: list[dict]) -> list[dict]:
    """Split knowledge articles into focused semantic chunks for vector indexing."""
    chunks = []
    for art in articles:
        content = art.get("content", "")
        # Split on double newline / sections
        sections = [s.strip() for s in content.split("\n\n") if s.strip()]
        for idx, section in enumerate(sections):
            chunk_id = f"{art['id']}-c{idx+1}"
            chunks.append({
                "chunk_id": chunk_id,
                "article_id": art["id"],
                "title": art["title"],
                "category": art["category"],
                "tags": art.get("tags", []),
                "text": f"Article: {art['title']} (Category: {art['category']})\n{section}",
                "excerpt": section[:240] + ("..." if len(section) > 240 else ""),
            })
    return chunks

