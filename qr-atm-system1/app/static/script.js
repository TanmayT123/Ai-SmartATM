// script.js

document.addEventListener('DOMContentLoaded', () => {
  const authForm = document.getElementById('authForm');
  const phoneInput = document.getElementById('phone');
  const pinInput = document.getElementById('pin');
  const video = document.getElementById('video');
  const canvas = document.getElementById('canvas');
  const captureBtn = document.getElementById('captureBtn');

  let stream = null;

  authForm.addEventListener('submit', async (e) => {
    e.preventDefault();

    const phone = phoneInput.value.trim();
    const pin = pinInput.value.trim();

    if (!phone || !pin) {
      alert("Please enter phone and PIN");
      return;
    }

    // Verify user with backend
    const res = await fetch('/verify-user', {
      method: 'POST',
      headers: {'Content-Type': 'application/json'},
      body: JSON.stringify({phone, pin})
    });

    const data = await res.json();

    if (data.success) {
      // Hide auth form, show webcam & capture button
      document.getElementById('verify-section').style.display = 'none';
      video.style.display = 'block';
      captureBtn.style.display = 'inline-block';

      try {
        stream = await navigator.mediaDevices.getUserMedia({video: true, audio: false});
        video.srcObject = stream;
      } catch (err) {
        alert('Error accessing webcam: ' + err.message);
      }
    } else {
      alert('Invalid phone or PIN!');
    }
  });

  captureBtn.addEventListener('click', () => {
    if (!stream) {
      alert('Webcam not started');
      return;
    }

    const phone = phoneInput.value.trim();

    canvas.width = video.videoWidth;
    canvas.height = video.videoHeight;

    const ctx = canvas.getContext('2d');
    ctx.drawImage(video, 0, 0, canvas.width, canvas.height);

    const imageBase64 = canvas.toDataURL('image/png');

    fetch('/register-face', {
      method: 'POST',
      headers: {'Content-Type': 'application/json'},
      body: JSON.stringify({
        phone: phone,
        image: imageBase64
      })
    })
    .then(res => res.json())
    .then(data => {
      alert(data.message);
      // Stop webcam
      if (stream) {
        stream.getTracks().forEach(track => track.stop());
      }
      video.style.display = 'none';
      captureBtn.style.display = 'none';
      document.getElementById('verify-section').style.display = 'block';
      phoneInput.value = '';
      pinInput.value = '';
    })
    .catch(err => {
      alert('Error registering face: ' + err.message);
    });
  });
});
