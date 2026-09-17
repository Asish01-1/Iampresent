const studentIdInput = document.getElementById("studentId");
const faceImagesInput = document.getElementById("faceImages");
const imageCount = document.getElementById("imageCount");
const previewContainer = document.getElementById("previewContainer");
const proceedButton = document.getElementById("proceedEnrollment");
const enrollmentStatus = document.getElementById("enrollmentStatus");


// ==========================================
// Image Selection
// ==========================================

faceImagesInput.addEventListener("change", function () {

    const files = Array.from(faceImagesInput.files);

    imageCount.textContent =
        `${files.length} image${files.length !== 1 ? "s" : ""} selected.`;

    previewContainer.innerHTML = "";


    // Show warning immediately
    if (files.length < 10) {

        imageCount.textContent +=
            " Minimum 10 images required.";

    }

    if (files.length > 30) {

        imageCount.textContent +=
            " Maximum 30 images allowed.";

    }


    // Preview images
    files.forEach((file) => {

        const image = document.createElement("img");

        image.src = URL.createObjectURL(file);

        image.className = "gallery-preview";

        previewContainer.appendChild(image);

    });

});


// ==========================================
// Enrollment
// ==========================================

proceedButton.addEventListener("click", async function () {

    const studentId =
        studentIdInput.value.trim().toUpperCase();

    const files =
        Array.from(faceImagesInput.files);


    // -------------------------------
    // Validate Student ID
    // -------------------------------

    if (!studentId) {

        enrollmentStatus.textContent =
            "Please enter Student ID.";

        return;
    }


    // -------------------------------
    // Validate Image Count
    // -------------------------------

    if (files.length < 10 || files.length > 30) {

        enrollmentStatus.textContent =
            "Please select between 10 and 30 images.";

        return;
    }


    // -------------------------------
    // Prepare FormData
    // -------------------------------

    const formData = new FormData();

    formData.append("student_id", studentId);


    files.forEach((file) => {

        formData.append("images", file);

    });


    // -------------------------------
    // UI State
    // -------------------------------

    proceedButton.disabled = true;

    enrollmentStatus.textContent =
        "Processing images... Please wait.";


    try {

    const API_BASE =
        window.location.hostname === "localhost" &&
        window.location.port === "5500"
            ? "http://127.0.0.1:8000"
            : window.location.origin;

    const response = await fetch(
        `${API_BASE}/enrollment/gallery`,
        {
            method: "POST",
            body: formData
        }
    );
        const result = await response.json();


        if (!response.ok) {

            throw new Error(
                result.detail || "Enrollment failed."
            );

        }


        // -------------------------------
        // Success
        // -------------------------------

        enrollmentStatus.textContent =
            `Enrollment successful. ${result.embeddings_created} embeddings created.`;

        studentIdInput.value = "";

        faceImagesInput.value = "";

        imageCount.textContent =
            "No images selected.";

        previewContainer.innerHTML = "";


    } catch (error) {

        console.error(error);

        enrollmentStatus.textContent =
            error.message || "Something went wrong.";

    }


    proceedButton.disabled = false;

});
