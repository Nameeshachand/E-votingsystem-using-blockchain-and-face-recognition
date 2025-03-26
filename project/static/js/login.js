document.addEventListener("DOMContentLoaded", function () {
    const loginForm = document.getElementById("login-form");
    const captureButton = document.getElementById("capture-button");
    const video = document.getElementById("video");
    const canvas = document.getElementById("canvas");

    let capturedImage = null; // Store captured image

    // Start video stream for face capture
    navigator.mediaDevices.getUserMedia({ video: true }).then((stream) => {
        video.srcObject = stream;
    }).catch((err) => console.error("Error accessing camera:", err));

    // Capture face photo
    captureButton.addEventListener("click", () => {
        canvas.width = video.videoWidth;
        canvas.height = video.videoHeight;

        const context = canvas.getContext("2d");
        context.drawImage(video, 0, 0, canvas.width, canvas.height);

        // Convert the canvas image to a Blob
        canvas.toBlob(blob => {
            capturedImage = blob; // Store captured image
            video.style.display = "none";
            canvas.style.display = "block";
        }, "image/jpeg");
    });

    // Handle form submission
    loginForm.addEventListener("submit", async function (event) {
        event.preventDefault();

        if (!capturedImage) {
            alert("Please capture your face before logging in.");
            return;
        }

        const formData = new FormData(loginForm);
        formData.append("face_image", capturedImage);

        try {
            const response = await fetch("/api/login", {
                method: "POST",
                body: formData
            });

            const result = await response.json();
            console.log("Server Response:", result); // Debugging Log

            alert(result.message);
            if (result.status === "success") {
                window.location.href = "/index";
            }
        } catch (error) {
            console.error("Login error:", error);
            alert("Error during login. Try again.");
        }
    });
});
