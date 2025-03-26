document.addEventListener("DOMContentLoaded", function () {
    const registerForm = document.getElementById("register-form");
    const captureButton = document.getElementById("capture-button");
    const video = document.getElementById("video");
    const canvas = document.getElementById("canvas");

    let capturedImage = null;

    // Start video stream for face capture
    navigator.mediaDevices.getUserMedia({ video: true }).then((stream) => {
        video.srcObject = stream;
    }).catch((err) => console.error("Error accessing camera:", err));

    // Capture photo on button click
    captureButton.addEventListener("click", () => {
        canvas.width = video.videoWidth;
        canvas.height = video.videoHeight;

        const context = canvas.getContext("2d");
        context.drawImage(video, 0, 0, canvas.width, canvas.height);

        // Convert the canvas image to a Blob
        canvas.toBlob(blob => {
            capturedImage = blob;  // Store the captured image
            // Hide video, show captured image
            video.style.display = "none";
            canvas.style.display = "block";
        }, "image/jpeg");
    });

    // Handle form submission
    registerForm.addEventListener("submit", async function (event) {
        event.preventDefault();
        
        if (!capturedImage) {
            alert("Please capture your face before submitting.");
            return;
        }

        const formData = new FormData(registerForm);
        formData.append("face_image", capturedImage);

        try {
            const response = await fetch("/api/register", {
                method: "POST",
                body: formData
            });

            const result = await response.json();
            alert(result.message);
            if (result.status === "success") {
                alert(`🎉 Registration Successful!\nYour Tracking ID: ${result.tracking_id}`);
                window.location.href = "/login";
            }
        } catch (error) {
            console.error("Registration error:", error);
            alert("Error during registration. Try again.");
        }
    });
});


