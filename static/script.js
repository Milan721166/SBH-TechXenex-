document.addEventListener("DOMContentLoaded", function () {
    const form = document.getElementById("loginForm");
    if (form) {
        form.addEventListener("submit", async function (event) {
            event.preventDefault();

            const username = document.getElementById("username").value;
            const password = document.getElementById("password").value;
            const role = window.location.pathname.split("_")[0].substring(1); // Get role from URL

            const response = await fetch("/login", {
                method: "POST",
                headers: {
                    "Content-Type": "application/json"
                },
                body: JSON.stringify({ username, password, role })
            });

            const data = await response.json();
            if (data.status === "success") {
                window.location.href = data.redirect;
            } else {
                document.getElementById("errorMessage").innerText = data.message;
            }
        });
    }
});
