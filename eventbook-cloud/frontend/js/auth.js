document.addEventListener("DOMContentLoaded", () => {
  const loginForm = document.getElementById("login-form");
  const registerForm = document.getElementById("register-form");
  if (loginForm) loginForm.addEventListener("submit", async e => {
    e.preventDefault();
    try {
      await api("/auth/login",{method:"POST",body:JSON.stringify({email:document.getElementById("email").value,password:document.getElementById("password").value})});
      location.href="/";
    } catch(err) { showAlert("#form-alert",err.message); }
  });
  if (registerForm) registerForm.addEventListener("submit", async e => {
    e.preventDefault();
    try {
      await api("/auth/register",{method:"POST",body:JSON.stringify({name:document.getElementById("name").value,email:document.getElementById("email").value,password:document.getElementById("password").value})});
      location.href="/";
    } catch(err) { showAlert("#form-alert",err.message); }
  });
});
