const authForm = document.getElementById("authForm");
const video = document.getElementById("video");
const canvas = document.getElementById("canvas");
const captureBtn = document.getElementById("captureBtn");

authForm.addEventListener("submit", async (e) => {
    e.preventDefault();

    const phone = document.getElementById("phone").value;
    const pin = document.getElementById("pin").value;

    const res = await fetch("/verify-user", {
        method: "POST",
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({phone, pin})
    });

    const result = await res.json();
    if (result.success) {
        startCamera();
    } else {
        alert("Invalid credentials");
    }
});

function startCamera() {
    navigator.mediaDevices.getUserMedia({ video: true })
        .then(stream => {
            video.srcObject = stream;
            video.style.display = "block";
            captureBtn.style.display = "block";
        })
        .catch(err => alert("Camera access denied: " + err));
}

captureBtn.addEventListener("click", async () => {
    canvas.style.display = "block";
    canvas.getContext('2d').drawImage(video, 0, 0, canvas.width = 300, canvas.height = 250);

    const base64Image = canvas.toDataURL('image/jpeg');
    const phone = document.getElementById("phone").value;

    const res = await fetch("/register-face", {
        method: "POST",
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({phone, image: base64Image})
    });

    const result = await res.json();
    alert(result.message);
});
