document.addEventListener("DOMContentLoaded", function() {

    const notifBtn = document.getElementById("notif-btn");
    const notifMenu = document.getElementById("notif-menu");

    notifBtn.addEventListener("click", function(e) {
        e.preventDefault();
        notifMenu.style.display = notifMenu.style.display === "block" ? "none" : "block";
    });

    document.addEventListener("click", function(e) {
        if (!notifBtn.contains(e.target) && !notifMenu.contains(e.target)) {
            notifMenu.style.display = "none";
        }
    });

});
