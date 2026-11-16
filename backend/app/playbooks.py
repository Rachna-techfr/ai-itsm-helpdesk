from __future__ import annotations

PLAYBOOKS: dict[str, dict] = {
    "vpn_repair": {
        "title": "Clear GlobalProtect credential cache and re-authenticate",
        "policy": "approval_required",
        "risk": "Restarts the user VPN agent. An analyst confirms before the cached password is cleared.",
        "steps": [
            {
                "name": "Check GlobalProtect service",
                "plan": "Query the PanGPS service on the caller laptop.",
                "result_if_run": "PanGPS is running. The last gateway response was error 809, user authentication failed.",
            },
            {
                "name": "Check gateway reachability",
                "plan": "Open a TLS check to vpn.northline.com:443.",
                "result_if_run": "vpn.northline.com answered. The path is up. This is an authentication failure, not an outage.",
            },
            {
                "name": "Compare Entra ID password change",
                "plan": "Read the password last-changed timestamp for the caller.",
                "result_if_run": "The password changed this morning. GlobalProtect still holds the pre-change credential blob.",
            },
            {
                "name": "Clear the VPN credential cache",
                "plan": "Remove the cached GlobalProtect credentials and restart PanGPS.",
                "result_if_run": "Cached credentials removed. PanGPS restarted and is waiting for a fresh sign-in.",
            },
            {
                "name": "Validate a new tunnel",
                "plan": "Confirm the gateway accepts the new password.",
                "result_if_run": "Simulated sign-in succeeded. Error 809 cleared and a user tunnel was issued.",
            },
        ],
    },
    "password_reset": {
        "title": "Issue a temporary Entra ID password",
        "policy": "auto",
        "risk": "Identity self-service. Policy allows an unattended reset when the account is not privileged.",
        "steps": [
            {
                "name": "Identify the account",
                "plan": "Match the caller to a single Entra ID user and confirm the password is expired.",
                "result_if_run": "Account enabled. Password-expired flag is set. No privileged roles.",
            },
            {
                "name": "Diagnose directory status",
                "plan": "Check lockout, recent failures, and the manager channel used to deliver a temporary password.",
                "result_if_run": "Not locked. Twelve failed sign-ins since expiry. Manager channel is available.",
            },
            {
                "name": "Search approved knowledge",
                "plan": "Retrieve the password-reset article before any write.",
                "result_if_run": "KB0002 authorizes a temporary password for an expired, non-privileged account.",
            },
            {
                "name": "Determine automation",
                "plan": "Compare confidence and the identity policy.",
                "result_if_run": "Confidence is above 0.85 and the playbook policy is auto. Unattended reset is allowed.",
            },
            {
                "name": "Execute the reset",
                "plan": "Generate a one-time password and revoke existing sessions.",
                "result_if_run": "Temporary password issued to the manager secure channel. Refresh tokens revoked.",
            },
            {
                "name": "Validate sign-in",
                "plan": "Run a simulated directory bind with the temporary password.",
                "result_if_run": "Bind succeeded. The user must choose a new password at the next sign-in.",
            },
        ],
    },
    "mfa_reset": {
        "title": "Reset Microsoft Authenticator registration",
        "policy": "auto",
        "risk": "Removes the current MFA method. Allowed unattended only for the caller's own standard account.",
        "steps": [
            {
                "name": "Identify the MFA method",
                "plan": "List registered authentication methods.",
                "result_if_run": "Microsoft Authenticator is registered and failing. No hardware key on the account.",
            },
            {
                "name": "Search approved knowledge",
                "plan": "Confirm KB0003 covers a lost or replaced phone.",
                "result_if_run": "KB0003 matches. The caller can re-register after the method is cleared.",
            },
            {
                "name": "Clear the authenticator method",
                "plan": "Delete the Microsoft Authenticator method and require re-registration.",
                "result_if_run": "Authenticator method removed. The next sign-in will prompt for a new registration.",
            },
            {
                "name": "Validate policy",
                "plan": "Confirm the account still satisfies the MFA conditional-access policy.",
                "result_if_run": "Conditional access still requires MFA. Sign-in is blocked until the user re-registers, as designed.",
            },
        ],
    },
    "account_unlock": {
        "title": "Unlock an Entra ID account",
        "policy": "auto",
        "risk": "Clears a lockout counter. Allowed unattended for standard employee accounts.",
        "steps": [
            {
                "name": "Confirm the lockout",
                "plan": "Read the sign-in log and lockout flag.",
                "result_if_run": "Smart lockout is active after repeated failures. The password itself is still valid.",
            },
            {
                "name": "Clear the lockout",
                "plan": "Reset the lockout counter in Entra ID.",
                "result_if_run": "Lockout cleared. The existing password was not changed.",
            },
            {
                "name": "Validate sign-in",
                "plan": "Simulate a single sign-in.",
                "result_if_run": "Sign-in succeeded. The caller was advised to wait two minutes before retrying VPN.",
            },
        ],
    },
    "outlook_repair": {
        "title": "Rebuild the Outlook cache",
        "policy": "approval_required",
        "risk": "Recreates the local OST. An analyst confirms so a large mailbox is not re-downloaded unattended.",
        "steps": [
            {
                "name": "Check Outlook connection status",
                "plan": "Read the Outlook profile connection state.",
                "result_if_run": "Desktop client is disconnected. Outlook on the web still sends and receives.",
            },
            {
                "name": "Compare the mailbox on the server",
                "plan": "Confirm the mailbox is healthy in Exchange Online.",
                "result_if_run": "Mailbox is accessible. The fault is the local cache, not the mailbox.",
            },
            {
                "name": "Rename the OST and restart Outlook",
                "plan": "Move the OST aside so Outlook rebuilds it.",
                "result_if_run": "OST renamed. Outlook restarted and began a cache rebuild.",
            },
            {
                "name": "Validate synchronization",
                "plan": "Send a probe message and confirm it appears in the desktop client.",
                "result_if_run": "Probe message arrived. Send/receive is current.",
            },
        ],
    },
    "printer_repair": {
        "title": "Clear the follow-me print queue",
        "policy": "approval_required",
        "risk": "Restarts the local spooler and cancels stuck jobs. An analyst confirms before jobs are purged.",
        "steps": [
            {
                "name": "Inspect the PaperCut queue",
                "plan": "Find jobs held for the caller badge.",
                "result_if_run": "Two jobs are held with status 'awaiting release'. The badge was read at Austin HQ Floor 4.",
            },
            {
                "name": "Clear stuck jobs",
                "plan": "Cancel the held jobs older than today.",
                "result_if_run": "Stuck jobs cancelled. The caller's new job is the only one in the queue.",
            },
            {
                "name": "Restart the print spooler",
                "plan": "Restart the spooler service on the caller laptop.",
                "result_if_run": "Spooler restarted. The PaperCut client reconnected.",
            },
            {
                "name": "Validate a test page",
                "plan": "Release a one-page test at the follow-me printer.",
                "result_if_run": "Test page released on Austin HQ MFP-04.",
            },
        ],
    },
    "disk_cleanup": {
        "title": "Clear temp files and Storage Sense",
        "policy": "auto",
        "risk": "Deletes only Windows temp files and the user temp folder. No profile documents are touched.",
        "steps": [
            {
                "name": "Measure free space",
                "plan": "Read free bytes on the operating-system drive.",
                "result_if_run": "C: has 4.2 GB free of 256 GB. The threshold for this laptop build is 15 GB.",
            },
            {
                "name": "Clear temp and delivery cache",
                "plan": "Remove Windows temp, user temp, and the Windows Update download cache.",
                "result_if_run": "18.6 GB reclaimed. Documents, Desktop, and Outlook data were not modified.",
            },
            {
                "name": "Validate free space",
                "plan": "Re-read the volume.",
                "result_if_run": "C: now has 22.8 GB free. The low-disk warning has cleared.",
            },
        ],
    },
    "service_restart": {
        "title": "Restart the named Windows service",
        "policy": "approval_required",
        "risk": "Restarts a single local service. An analyst confirms the service name before the restart.",
        "steps": [
            {
                "name": "Identify the service",
                "plan": "Map the symptom to a service on the standard laptop image.",
                "result_if_run": "The failing service is on the standard image and is safe to recycle.",
            },
            {
                "name": "Restart the service",
                "plan": "Stop and start the service, then read its state.",
                "result_if_run": "Service returned to Running. Dependent services recovered.",
            },
            {
                "name": "Validate the endpoint",
                "plan": "Run the service health check from the runbook.",
                "result_if_run": "Health check passed.",
            },
        ],
    },
}


def get_playbook(playbook_id: str | None) -> dict | None:
    if not playbook_id:
        return None
    book = PLAYBOOKS.get(playbook_id)
    return book
