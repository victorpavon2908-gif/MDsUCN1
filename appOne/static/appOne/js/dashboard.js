document.addEventListener("DOMContentLoaded", function() {
  const notifBtn = document.getElementById("notif-btn");
  const notifMenu = document.getElementById("notif-menu");
  const notifCount = document.getElementById("notif-count");

  notifBtn.addEventListener("click", function(e) {
    e.preventDefault();
    notifMenu.style.display = notifMenu.style.display === "block" ? "none" : "block";
  });

  document.addEventListener("click", function(e) {
    if (!notifBtn.contains(e.target) && !notifMenu.contains(e.target)) {
      notifMenu.style.display = "none";
    }
  });

  function updateNotifCount() {
    const items = document.querySelectorAll(".notif-item");
    if (items.length > 0) {
      notifCount.innerText = items.length;
    } else {
      notifCount.remove();
      notifMenu.innerHTML = '<li><a href="#">No hay notificaciones nuevas</a></li>';
    }
  }

  function handleNotifAction(action, userId, item) {
    fetch(`/usuarios/${action}/${userId}/`, { method: 'POST', headers: {'X-CSRFToken': csrftoken} })
      .then(res => {
        if (res.ok) {
          // Desvanecer la notificación
          item.style.opacity = '0';
          setTimeout(() => {
            item.remove();
            updateNotifCount();
          }, 300);
        }
      });
  }

  // Obtener CSRF token de la cookie
  const csrftoken = document.querySelector('[name=csrfmiddlewaretoken]').value;

  document.querySelectorAll(".notif-btn-approve").forEach(btn => {
    btn.addEventListener("click", function() {
      const userId = this.dataset.userId;
      const item = this.closest(".notif-item");
      handleNotifAction('aprobar_usuario', userId, item);
    });
  });

  document.querySelectorAll(".notif-btn-reject").forEach(btn => {
    btn.addEventListener("click", function() {
      const userId = this.dataset.userId;
      const item = this.closest(".notif-item");
      handleNotifAction('rechazar_usuario', userId, item);
    });
  });
});
