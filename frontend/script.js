const API = "http://127.0.0.1:8000";


// ==========================================
// ELEMENTS
// ==========================================

// Student form
const studentForm =
    document.getElementById("studentForm");

const studentMessage =
    document.getElementById("studentMessage");

const addStudentButton =
    document.getElementById("addStudentButton");


// ==========================================
// ENROLLMENT
// ==========================================

const enrollmentSection =
    document.getElementById("enrollmentSection");

const enrollmentCamera =
    document.getElementById("enrollmentCamera");

const enrollmentPlaceholder =
    document.getElementById(
        "enrollmentPlaceholder"
    );

const startEnrollmentCameraButton =
    document.getElementById(
        "startEnrollmentCamera"
    );

const captureButton =
    document.getElementById(
        "captureButton"
    );

const captureCount =
    document.getElementById(
        "captureCount"
    );

const enrollButton =
    document.getElementById(
        "enrollButton"
    );

const enrollmentMessage =
    document.getElementById(
        "enrollmentMessage"
    );


// ==========================================
// DAILY RECOGNITION
// ==========================================

const camera =
    document.getElementById("camera");

const cameraPlaceholder =
    document.getElementById(
        "cameraPlaceholder"
    );

const startCameraButton =
    document.getElementById(
        "startCamera"
    );

const stopCameraButton =
    document.getElementById(
        "stopCamera"
    );

const recognitionMessage =
    document.getElementById(
        "recognitionMessage"
    );


// ==========================================
// DETECTED STUDENTS
// ==========================================

const studentList =
    document.getElementById(
        "studentList"
    );

const studentCount =
    document.getElementById(
        "studentCount"
    );

const proceedButton =
    document.getElementById(
        "proceedButton"
    );

const attendanceMessage =
    document.getElementById(
        "attendanceMessage"
    );


// ==========================================
// REPORT ELEMENTS
// ==========================================

const viewTodayButton =
    document.getElementById(
        "viewTodayButton"
    );

const downloadTodayButton =
    document.getElementById(
        "downloadTodayButton"
    );

const todayReport =
    document.getElementById(
        "todayReport"
    );


const verificationDate =
    document.getElementById(
        "verificationDate"
    );

const viewVerificationButton =
    document.getElementById(
        "viewVerificationButton"
    );

const downloadVerificationButton =
    document.getElementById(
        "downloadVerificationButton"
    );

const verificationReport =
    document.getElementById(
        "verificationReport"
    );


const reportMonth =
    document.getElementById(
        "reportMonth"
    );

const reportYear =
    document.getElementById(
        "reportYear"
    );

const viewMonthlyButton =
    document.getElementById(
        "viewMonthlyButton"
    );

const downloadMonthlyButton =
    document.getElementById(
        "downloadMonthlyButton"
    );

const monthlyReport =
    document.getElementById(
        "monthlyReport"
    );


const reportStudentId =
    document.getElementById(
        "reportStudentId"
    );

const studentFromDate =
    document.getElementById(
        "studentFromDate"
    );

const studentToDate =
    document.getElementById(
        "studentToDate"
    );

const viewStudentReportButton =
    document.getElementById(
        "viewStudentReportButton"
    );

const downloadStudentReportButton =
    document.getElementById(
        "downloadStudentReportButton"
    );

const studentReport =
    document.getElementById(
        "studentReport"
    );


// ==========================================
// VARIABLES
// ==========================================

// Enrollment
let enrollmentStream = null;

let enrollmentImages = [];

let currentStudentId = null;

let currentStudentName = null;

let currentClassName = null;


// Daily recognition
let cameraStream = null;

let recognitionTimer = null;

let recognitionSessionTimer = null;

let recognitionBusy = false;


// Students detected during current page/day
let detectedStudents = new Map();


// Students already logged during
// current recognition session
let loggedStudentsThisSession = new Set();


// Current recognition session start
let currentSessionStart = null;


// ==========================================
// RECOGNITION SETTINGS
// ==========================================

const RECOGNITION_DELAY = 700;

const SESSION_DURATION =
    10 * 60 * 1000;


// ==========================================
// DEFAULT REPORT DATES
// ==========================================

function getTodayString() {

    const now = new Date();

    const year =
        now.getFullYear();

    const month =
        String(
            now.getMonth() + 1
        ).padStart(2, "0");

    const day =
        String(
            now.getDate()
        ).padStart(2, "0");

    return `${year}-${month}-${day}`;
}


function setDefaultReportDates() {

    const today =
        getTodayString();

    verificationDate.value =
        today;

    studentFromDate.value =
        today;

    studentToDate.value =
        today;

    reportYear.value =
        new Date().getFullYear();

    reportMonth.value =
        new Date().getMonth() + 1;
}


setDefaultReportDates();


// ==========================================
// ADD STUDENT
// ==========================================

studentForm.addEventListener(
    "submit",
    async (event) => {

        event.preventDefault();

        const studentId =
            document
                .getElementById(
                    "studentId"
                )
                .value
                .trim();

        const studentName =
            document
                .getElementById(
                    "studentName"
                )
                .value
                .trim();

        const className =
            document
                .getElementById(
                    "className"
                )
                .value
                .trim();

        if (
            !studentId ||
            !studentName
        ) {

            studentMessage.textContent =
                "Student ID and name are required.";

            return;
        }

        addStudentButton.disabled =
            true;

        studentMessage.textContent =
            "Adding student...";

        try {

            const response =
                await fetch(
                    `${API}/students`,
                    {
                        method: "POST",

                        headers: {
                            "Content-Type":
                                "application/json"
                        },

                        body:
                            JSON.stringify({

                                student_id:
                                    studentId,

                                name:
                                    studentName,

                                class_name:
                                    className ||
                                    null
                            })
                    }
                );

            let data = {};

            try {

                data =
                    await response.json();

            }
            catch {

                data = {};
            }

            if (!response.ok) {

                let errorMessage =
                    data.detail ||
                    data.message ||
                    "Failed to add student.";

                if (
                    Array.isArray(
                        data.detail
                    )
                ) {

                    errorMessage =
                        data.detail
                            .map(
                                item =>
                                    item.msg
                            )
                            .join(", ");
                }

                throw new Error(
                    errorMessage
                );
            }

            currentStudentId =
                studentId.toUpperCase();

            currentStudentName =
                studentName;

            currentClassName =
                className;

            studentMessage.textContent =
                `Student ${studentName} added successfully.`;

            enrollmentSection.classList.remove(
                "hidden"
            );

            studentForm
                .querySelectorAll(
                    "input"
                )
                .forEach(
                    input => {
                        input.disabled =
                            true;
                    }
                );

            addStudentButton.disabled =
                true;

            enrollmentMessage.textContent =
                "Student ready. Start the camera.";

            // loadStudentsForReport();

        }
        catch (error) {

            console.error(
                "Add student error:",
                error
            );

            if (
                error instanceof TypeError &&
                error.message ===
                    "Failed to fetch"
            ) {

                studentMessage.textContent =
                    "Cannot connect to FastAPI. Make sure Uvicorn is running.";

            }
            else {

                studentMessage.textContent =
                    error.message;
            }

            addStudentButton.disabled =
                false;
        }
    }
);


// ==========================================
// START ENROLLMENT CAMERA
// ==========================================

startEnrollmentCameraButton.addEventListener(
    "click",
    async () => {

        try {

            enrollmentStream =
                await navigator
                    .mediaDevices
                    .getUserMedia({

                        video: {
                            width: 640,
                            height: 480
                        },

                        audio: false
                    });

            enrollmentCamera.srcObject =
                enrollmentStream;

            enrollmentCamera.style.display =
                "block";

            enrollmentPlaceholder.style.display =
                "none";

            startEnrollmentCameraButton.disabled =
                true;

            captureButton.disabled =
                false;

            enrollmentMessage.textContent =
                "Camera started. Capture 30 images.";

        }
        catch (error) {

            console.error(
                "Enrollment camera error:",
                error
            );

            enrollmentMessage.textContent =
                "Could not access camera. Check browser camera permission.";
        }
    }
);


// ==========================================
// CAPTURE ENROLLMENT IMAGE
// ==========================================

captureButton.addEventListener(
    "click",
    async () => {

        if (
            !enrollmentStream ||
            enrollmentCamera.videoWidth === 0 ||
            enrollmentCamera.videoHeight === 0
        ) {

            enrollmentMessage.textContent =
                "Camera is not ready yet.";

            return;
        }

        if (
            enrollmentImages.length >= 30
        ) {

            return;
        }

        const canvas =
            document.createElement(
                "canvas"
            );

        canvas.width =
            enrollmentCamera.videoWidth;

        canvas.height =
            enrollmentCamera.videoHeight;

        const context =
            canvas.getContext(
                "2d"
            );

        context.drawImage(
            enrollmentCamera,
            0,
            0,
            canvas.width,
            canvas.height
        );

        const blob =
            await new Promise(
                resolve => {

                    canvas.toBlob(
                        resolve,
                        "image/jpeg",
                        0.85
                    );

                }
            );

        if (!blob) {

            enrollmentMessage.textContent =
                "Could not capture image.";

            return;
        }

        enrollmentImages.push(
            blob
        );

        captureCount.textContent =
            enrollmentImages.length;

        enrollmentMessage.textContent =
            `Captured ${enrollmentImages.length} of 30 images.`;

        if (
            enrollmentImages.length >= 30
        ) {

            captureButton.disabled =
                true;

            enrollButton.disabled =
                false;

            enrollmentMessage.textContent =
                "30 images captured. You can now enroll the student.";
        }
    }
);


// ==========================================
// ENROLL STUDENT
// ==========================================

enrollButton.addEventListener(
    "click",
    async () => {

        if (
            enrollmentImages.length !== 30
        ) {

            enrollmentMessage.textContent =
                "Please capture all 30 images first.";

            return;
        }

        if (!currentStudentId) {

            enrollmentMessage.textContent =
                "No student selected for enrollment.";

            return;
        }

        enrollButton.disabled =
            true;

        enrollmentMessage.textContent =
            "Uploading images and creating AI embeddings...";

        const formData =
            new FormData();

        formData.append(
            "student_id",
            currentStudentId
        );

        enrollmentImages.forEach(
            (image, index) => {

                formData.append(
                    "images",
                    image,
                    `face_${index + 1}.jpg`
                );
            }
        );

        try {

            const response =
                await fetch(
                    `${API}/enrollment`,
                    {
                        method: "POST",
                        body: formData
                    }
                );

            let data = {};

            try {

                data =
                    await response.json();

            }
            catch {

                data = {};
            }

            if (!response.ok) {

                let errorMessage =
                    data.detail ||
                    data.message ||
                    "Enrollment failed.";

                if (
                    Array.isArray(
                        data.detail
                    )
                ) {

                    errorMessage =
                        data.detail
                            .map(
                                item =>
                                    item.msg
                            )
                            .join(", ");
                }

                throw new Error(
                    errorMessage
                );
            }

            if (
                data.success === false
            ) {

                throw new Error(
                    data.message ||
                    "Enrollment failed."
                );
            }

            enrollmentMessage.textContent =
                data.message ||
                "Student enrolled successfully!";

            enrollButton.textContent =
                "Enrollment Complete";

            enrollButton.disabled =
                true;

            captureButton.disabled =
                true;

            if (enrollmentStream) {

                enrollmentStream
                    .getTracks()
                    .forEach(
                        track => {
                            track.stop();
                        }
                    );

                enrollmentStream =
                    null;
            }

            enrollmentCamera.srcObject =
                null;

            loadStudentsForReport();

        }
        catch (error) {

            console.error(
                "Enrollment error:",
                error
            );

            if (
                error instanceof TypeError &&
                error.message ===
                    "Failed to fetch"
            ) {

                enrollmentMessage.textContent =
                    "Cannot connect to FastAPI. Make sure Uvicorn is running.";

            }
            else {

                enrollmentMessage.textContent =
                    `Enrollment failed: ${error.message}`;
            }

            enrollButton.disabled =
                false;
        }
    }
);


// ==========================================
// CAPTURE RECOGNITION FRAME
// ==========================================

function captureRecognitionFrame() {

    if (
        !cameraStream ||
        camera.videoWidth === 0 ||
        camera.videoHeight === 0
    ) {

        return null;
    }

    const canvas =
        document.createElement(
            "canvas"
        );

    canvas.width =
        camera.videoWidth;

    canvas.height =
        camera.videoHeight;

    const context =
        canvas.getContext(
            "2d"
        );

    context.drawImage(
        camera,
        0,
        0,
        canvas.width,
        canvas.height
    );

    return new Promise(
        resolve => {

            canvas.toBlob(
                blob => {
                    resolve(blob);
                },
                "image/jpeg",
                0.80
            );

        }
    );
}


// ==========================================
// UPDATE STUDENT LIST
// ==========================================

function updateStudentList() {

    studentList.innerHTML =
        "";

    const students =
        Array.from(
            detectedStudents.values()
        );

    studentCount.textContent =
        students.length;

    if (
        students.length === 0
    ) {

        studentList.innerHTML =
            "<p>No students recognized yet.</p>";

        proceedButton.disabled =
            true;

        return;
    }

    students.forEach(
        student => {

            const item =
                document.createElement(
                    "div"
                );

            item.className =
                "student-item";

            item.innerHTML = `

                <strong>
                    ${student.name}
                </strong>

                <span>
                    ID: ${student.student_id}
                </span>

                <span>
                    ${student.class_name || ""}
                </span>

                <span>
                    Matching accuracy:
                    ${student.score}
                </span>
            `;

            studentList.appendChild(
                item
            );
        }
    );

    proceedButton.disabled =
        false;
}


// ==========================================
// SAVE RECOGNITION VERIFICATION LOG
// ==========================================

async function saveRecognitionLog(
    studentId
) {

    if (!currentSessionStart) {

        return;
    }

    try {

        await fetch(
            `${API}/recognition/log`,
            {

                method: "POST",

                headers: {
                    "Content-Type":
                        "application/json"
                },

                body:
                    JSON.stringify({

                        student_id:
                            studentId,

                        session_start:
                            currentSessionStart
                    })
            }
        );

    }
    catch (error) {

        console.error(
            "Recognition log error:",
            error
        );
    }
}


// ==========================================
// PROCESS RECOGNITION
// ==========================================

function processRecognition(
    faces
) {

    faces.forEach(
        face => {

            if (
                !face.recognized ||
                !face.student
            ) {

                return;
            }

            const student =
                face.student;

            const studentId =
                reportStudentId.value.trim().toUpperCase();

            detectedStudents.set(
                studentId,
                {
                    ...student,
                    score: face.score
                }
            );


            // Log this student only once
            // during the current camera session.

            if (
                !loggedStudentsThisSession.has(
                    studentId
                )
            ) {

                loggedStudentsThisSession.add(
                    studentId
                );

                saveRecognitionLog(
                    studentId
                );
            }

        }
    );

    updateStudentList();
}


// ==========================================
// SEND FRAME TO FASTAPI
// ==========================================

async function recognizeCurrentFrame() {

    if (
        recognitionBusy ||
        !cameraStream
    ) {

        return;
    }

    recognitionBusy =
        true;

    try {

        const blob =
            await captureRecognitionFrame();

        if (!blob) {

            return;
        }

        const formData =
            new FormData();

        formData.append(
            "image",
            blob,
            "recognition.jpg"
        );

        const response =
            await fetch(
                `${API}/recognition`,
                {
                    method: "POST",
                    body: formData
                }
            );

        if (!response.ok) {

            throw new Error(
                "Recognition request failed."
            );
        }

        const data =
            await response.json();

        if (!data.success) {

            recognitionMessage.textContent =
                data.message ||
                "Recognition failed.";

            return;
        }

        if (
            data.face_count === 0
        ) {

            recognitionMessage.textContent =
                "No face detected.";

            return;
        }

        processRecognition(
            data.faces || []
        );

        const recognizedFaces =
            (data.faces || [])
                .filter(
                    face =>
                        face.recognized &&
                        face.student
                );

        if (
            recognizedFaces.length > 0
        ) {

            const first =
                recognizedFaces[0];

            recognitionMessage.textContent =
                `Faces detected: ${data.face_count} | ` +
                `Matched: ${first.student.student_id} | ` +
                `Score: ${first.score}`;

        }
        else {

            recognitionMessage.textContent =
                `Faces detected: ${data.face_count} | ` +
                `No student matched.`;
        }

    }
    catch (error) {

        console.error(
            "Recognition error:",
            error
        );

        recognitionMessage.textContent =
            "Recognition connection error.";

    }
    finally {

        recognitionBusy =
            false;
    }
}


// ==========================================
// START RECOGNITION LOOP
// ==========================================

function startRecognitionLoop() {

    if (recognitionTimer) {

        clearInterval(
            recognitionTimer
        );
    }

    recognitionTimer =
        setInterval(
            recognizeCurrentFrame,
            RECOGNITION_DELAY
        );

    recognizeCurrentFrame();
}


// ==========================================
// STOP RECOGNITION SESSION
// ==========================================

function stopRecognitionSession() {

    if (recognitionTimer) {

        clearInterval(
            recognitionTimer
        );

        recognitionTimer =
            null;
    }

    if (cameraStream) {

        cameraStream
            .getTracks()
            .forEach(
                track => {
                    track.stop();
                }
            );

        cameraStream =
            null;
    }

    camera.srcObject =
        null;

    camera.style.display =
        "none";

    cameraPlaceholder.style.display =
        "flex";

    startCameraButton.disabled =
        false;

    stopCameraButton.disabled =
        true;

    recognitionSessionTimer =
        null;

    currentSessionStart =
        null;

    loggedStudentsThisSession =
        new Set();

    recognitionMessage.textContent =
        `10-minute recognition complete. ${detectedStudents.size} student(s) detected.`;

    updateStudentList();
}


// ==========================================
// START DAILY CAMERA
// ==========================================

startCameraButton.addEventListener(
    "click",
    async () => {

        try {

            cameraStream =
                await navigator
                    .mediaDevices
                    .getUserMedia({

                        video: {
                            width: 640,
                            height: 480
                        },

                        audio: false
                    });

            camera.srcObject =
                cameraStream;

            camera.style.display =
                "block";

            cameraPlaceholder.style.display =
                "none";

            startCameraButton.disabled =
                true;

            stopCameraButton.disabled =
                false;


            // New session
            currentSessionStart =
                new Date().toISOString();


            // New session gets its own
            // verification log set.

            loggedStudentsThisSession =
                new Set();


            // IMPORTANT:
            // detectedStudents is NOT cleared.
            //
            // This allows:
            //
            // Session 1 -> 001, 002
            // Session 2 -> 002, 003
            //
            // Final -> 001, 002, 003

            updateStudentList();

            recognitionMessage.textContent =
                "Camera started. Recognizing students for 10 minutes...";

            startRecognitionLoop();


            if (recognitionSessionTimer) {

                clearTimeout(
                    recognitionSessionTimer
                );
            }

            recognitionSessionTimer =
                setTimeout(
                    () => {

                        stopRecognitionSession();

                    },
                    SESSION_DURATION
                );

        }
        catch (error) {

            console.error(
                "Daily camera error:",
                error
            );

            recognitionMessage.textContent =
                "Could not access camera. Check browser camera permission.";
        }
    }
);


// ==========================================
// STOP DAILY CAMERA MANUALLY
// ==========================================

stopCameraButton.addEventListener(
    "click",
    () => {

        if (recognitionTimer) {

            clearInterval(
                recognitionTimer
            );

            recognitionTimer =
                null;
        }

        if (recognitionSessionTimer) {

            clearTimeout(
                recognitionSessionTimer
            );

            recognitionSessionTimer =
                null;
        }

        if (cameraStream) {

            cameraStream
                .getTracks()
                .forEach(
                    track => {
                        track.stop();
                    }
                );

            cameraStream =
                null;
        }

        camera.srcObject =
            null;

        camera.style.display =
            "none";

        cameraPlaceholder.style.display =
            "flex";

        startCameraButton.disabled =
            false;

        stopCameraButton.disabled =
            true;

        currentSessionStart =
            null;

        loggedStudentsThisSession =
            new Set();

        recognitionMessage.textContent =
            `Recognition stopped. ${detectedStudents.size} student(s) detected.`;

        updateStudentList();
    }
);


// ==========================================
// PROCEED ATTENDANCE
// ==========================================

proceedButton.addEventListener(
    "click",
    async () => {

        const studentIds =
            Array.from(
                detectedStudents.keys()
            );

        if (
            studentIds.length === 0
        ) {

            attendanceMessage.textContent =
                "No students detected.";

            return;
        }

        proceedButton.disabled =
            true;

        attendanceMessage.textContent =
            "Recording attendance...";

        try {

            const response =
                await fetch(
                    `${API}/attendance/proceed`,
                    {

                        method: "POST",

                        headers: {
                            "Content-Type":
                                "application/json"
                        },

                        body:
                            JSON.stringify({

                                student_ids:
                                    studentIds
                            })
                    }
                );

            let data = {};

            try {

                data =
                    await response.json();

            }
            catch {

                data = {};
            }

            if (!response.ok) {

                let errorMessage =
                    data.detail ||
                    data.message ||
                    "Attendance failed.";

                if (
                    Array.isArray(
                        data.detail
                    )
                ) {

                    errorMessage =
                        data.detail
                            .map(
                                item =>
                                    item.msg
                            )
                            .join(", ");
                }

                throw new Error(
                    errorMessage
                );
            }

            attendanceMessage.textContent =
                data.message ||
                `Attendance recorded for ${studentIds.length} student(s).`;

        }
        catch (error) {

            console.error(
                "Attendance error:",
                error
            );

            if (
                error instanceof TypeError &&
                error.message ===
                    "Failed to fetch"
            ) {

                attendanceMessage.textContent =
                    "Cannot connect to FastAPI.";

            }
            else {

                attendanceMessage.textContent =
                    error.message;
            }

            proceedButton.disabled =
                false;
        }
    }
);


// ==========================================
// LOAD STUDENTS FOR REPORT DROPDOWN
// ==========================================

async function loadStudentsForReport() {

    try {

        const response =
            await fetch(
                `${API}/students`
            );

        if (!response.ok) {

            throw new Error(
                "Could not load students."
            );
        }

        const students =
            await response.json();

        reportStudent.innerHTML =
            `<option value="">
                Select student
            </option>`;

        students.forEach(
            student => {

                const option =
                    document.createElement(
                        "option"
                    );

                option.value =
                    student.student_id;

                option.textContent =
                    `${student.student_id} - ${student.name}`;

                reportStudent.appendChild(
                    option
                );
            }
        );

    }
    catch (error) {

        console.error(
            "Student loading error:",
            error
        );
    }
}


// Load on page start
loadStudentsForReport();


// ==========================================
// VIEW TODAY ATTENDANCE
// ==========================================

viewTodayButton.addEventListener(
    "click",
    async () => {

        todayReport.innerHTML =
            "Loading...";

        try {

            const response =
                await fetch(
                    `${API}/attendance/today`
                );

            const data =
                await response.json();

            if (!response.ok) {

                throw new Error(
                    data.message ||
                    "Could not load attendance."
                );
            }

            const rows =
                data.attendance || [];

            if (
                rows.length === 0
            ) {

                todayReport.innerHTML =
                    "<p>No attendance recorded today.</p>";

                return;
            }

            let html = `

                <h4>
                    Attendance:
                    ${data.date}
                </h4>

                <table>

                    <thead>

                        <tr>
                            <th>Student ID</th>
                            <th>Name</th>
                            <th>Class</th>
                            <th>Status</th>
                        </tr>

                    </thead>

                    <tbody>
            `;

            rows.forEach(
                row => {

                    html += `

                        <tr>

                            <td>
                                ${row.student_id}
                            </td>

                            <td>
                                ${row.name}
                            </td>

                            <td>
                                ${row.class_name || ""}
                            </td>

                            <td>
                                ${
                                    row.present
                                    ? "Present"
                                    : "Absent"
                                }
                            </td>

                        </tr>
                    `;
                }
            );

            html += `

                    </tbody>

                </table>
            `;

            todayReport.innerHTML =
                html;

        }
        catch (error) {

            console.error(
                "Today report error:",
                error
            );

            todayReport.innerHTML =
                `<p>${error.message}</p>`;
        }
    }
);


// ==========================================
// DOWNLOAD TODAY
// ==========================================

downloadTodayButton.addEventListener(
    "click",
    () => {

        window.open(
            `${API}/attendance/today/download`,
            "_blank"
        );
    }
);


// ==========================================
// VIEW RECOGNITION VERIFICATION
// ==========================================

viewVerificationButton.addEventListener(
    "click",
    async () => {

        const selectedDate =
            verificationDate.value;

        if (!selectedDate) {

            verificationReport.innerHTML =
                "<p>Select a date first.</p>";

            return;
        }

        verificationReport.innerHTML =
            "Loading...";

        try {

            const response =
                await fetch(
                    `${API}/recognition/logs?log_date=${selectedDate}`
                );

            const data =
                await response.json();

            if (!response.ok) {

                throw new Error(
                    data.message ||
                    "Could not load verification."
                );
            }

            const rows =
                data.logs || [];

            if (
                rows.length === 0
            ) {

                verificationReport.innerHTML =
                    "<p>No recognition logs found for this date.</p>";

                return;
            }

            let html = `

                <h4>
                    Recognition Verification:
                    ${selectedDate}
                </h4>

                <table>

                    <thead>

                        <tr>

                            <th>
                                Recognition Time
                            </th>

                            <th>
                                Student ID
                            </th>

                            <th>
                                Name
                            </th>

                            <th>
                                Class
                            </th>

                            <th>
                                Session Start
                            </th>

                        </tr>

                    </thead>

                    <tbody>
            `;

            rows.forEach(
                row => {

                    html += `

                        <tr>

                            <td>
                                ${formatDateTime(
                                    row.recognized_at
                                )}
                            </td>

                            <td>
                                ${row.student_id}
                            </td>

                            <td>
                                ${row.name}
                            </td>

                            <td>
                                ${row.class_name || ""}
                            </td>

                            <td>
                                ${formatDateTime(
                                    row.session_start
                                )}
                            </td>

                        </tr>
                    `;
                }
            );

            html += `

                    </tbody>

                </table>
            `;

            verificationReport.innerHTML =
                html;

        }
        catch (error) {

            console.error(
                "Verification error:",
                error
            );

            verificationReport.innerHTML =
                `<p>${error.message}</p>`;
        }
    }
);


// ==========================================
// DOWNLOAD VERIFICATION
// ==========================================

downloadVerificationButton.addEventListener(
    "click",
    () => {

        const selectedDate =
            verificationDate.value;

        if (!selectedDate) {

            alert(
                "Select a date first."
            );

            return;
        }

        window.open(
            `${API}/recognition/logs/download?log_date=${selectedDate}`,
            "_blank"
        );
    }
);


// ==========================================
// VIEW MONTHLY REPORT
// ==========================================

viewMonthlyButton.addEventListener(
    "click",
    async () => {

        const month =
            Number(
                reportMonth.value
            );

        const year =
            Number(
                reportYear.value
            );

        if (!month || !year) {

            monthlyReport.innerHTML =
                "<p>Select month and year.</p>";

            return;
        }

        monthlyReport.innerHTML =
            "Loading...";

        try {

            const response =
                await fetch(
                    `${API}/reports/monthly?year=${year}&month=${month}`
                );

            const data =
                await response.json();

            if (!response.ok) {

                throw new Error(
                    data.message ||
                    "Could not load monthly report."
                );
            }

            const rows =
                data.report || [];

            let html = `

                <h4>
                    Monthly Report:
                    ${monthName(month)}
                    ${year}
                </h4>

                <table>

                    <thead>

                        <tr>

                            <th>
                                Student ID
                            </th>

                            <th>
                                Name
                            </th>

                            <th>
                                Class
                            </th>

                            <th>
                                Present
                            </th>

                        </tr>

                    </thead>

                    <tbody>
            `;

            rows.forEach(
                row => {

                    html += `

                        <tr>

                            <td>
                                ${row.student_id}
                            </td>

                            <td>
                                ${row.name}
                            </td>

                            <td>
                                ${row.class_name || ""}
                            </td>

                            <td>
                                ${row.present}
                            </td>

                        </tr>
                    `;
                }
            );

            html += `

                    </tbody>

                </table>
            `;

            monthlyReport.innerHTML =
                html;

        }
        catch (error) {

            console.error(
                "Monthly report error:",
                error
            );

            monthlyReport.innerHTML =
                `<p>${error.message}</p>`;
        }
    }
);


// ==========================================
// DOWNLOAD MONTHLY
// ==========================================

downloadMonthlyButton.addEventListener(
    "click",
    () => {

        const month =
            Number(
                reportMonth.value
            );

        const year =
            Number(
                reportYear.value
            );

        if (!month || !year) {

            alert(
                "Select month and year."
            );

            return;
        }

        window.open(
            `${API}/reports/monthly/download?year=${year}&month=${month}`,
            "_blank"
        );
    }
);


// ==========================================
// VIEW STUDENT REPORT
// ==========================================

viewStudentReportButton.addEventListener(
    "click",
    async () => {

        const studentId =
            reportStudent.value;

        const fromDate =
            studentFromDate.value;

        const toDate =
            studentToDate.value;

        if (
            !studentId ||
            !fromDate ||
            !toDate
        ) {

            studentReport.innerHTML =
                "<p>Select student and dates.</p>";

            return;
        }

        if (
            fromDate > toDate
        ) {

            studentReport.innerHTML =
                "<p>From date cannot be after To date.</p>";

            return;
        }

        studentReport.innerHTML =
            "Loading...";

        try {

            const response =
                await fetch(
                    `${API}/reports/student?student_id=${encodeURIComponent(studentId)}&from_date=${fromDate}&to_date=${toDate}`
                );

            const data =
                await response.json();

            if (!response.ok) {

                throw new Error(
                    data.message ||
                    "Could not load student report."
                );
            }

            if (!data.success) {

                throw new Error(
                    data.message ||
                    "Could not load student report."
                );
            }

            const student =
                data.student;

            const rows =
                data.records || [];

            let html = `

                <h4>
                    ${student.name}
                    (${student.student_id})
                </h4>

                <p>
                    From:
                    ${data.from_date}
                    &nbsp;&nbsp;
                    To:
                    ${data.to_date}
                </p>

                <p>
                    <strong>
                        Present:
                    </strong>
                    ${data.present}

                    &nbsp;&nbsp;

                    <strong>
                        Absent:
                    </strong>
                    ${data.absent}
                </p>
            `;

            if (
                rows.length === 0
            ) {

                html +=
                    "<p>No attendance records found.</p>";

            }
            else {

                html += `

                    <table>

                        <thead>

                            <tr>

                                <th>
                                    Date
                                </th>

                                <th>
                                    Status
                                </th>

                            </tr>

                        </thead>

                        <tbody>
                `;

                rows.forEach(
                    row => {

                        html += `

                            <tr>

                                <td>
                                    ${row.attendance_date}
                                </td>

                                <td>
                                    ${
                                        row.present
                                        ? "Present"
                                        : "Absent"
                                    }
                                </td>

                            </tr>
                        `;
                    }
                );

                html += `

                        </tbody>

                    </table>
                `;
            }

            studentReport.innerHTML =
                html;

        }
        catch (error) {

            console.error(
                "Student report error:",
                error
            );

            studentReport.innerHTML =
                `<p>${error.message}</p>`;
        }
    }
);


// ==========================================
// DOWNLOAD STUDENT REPORT
// ==========================================

downloadStudentReportButton.addEventListener(
    "click",
    () => {

        const studentId =
    reportStudentId.value.trim().toUpperCase();

        const fromDate =
            studentFromDate.value;

        const toDate =
            studentToDate.value;

        if (
            !studentId ||
            !fromDate ||
            !toDate
        ) {

            alert(
                "Select student and dates."
            );

            return;
        }

        if (
            fromDate > toDate
        ) {

            alert(
                "From date cannot be after To date."
            );

            return;
        }

        window.open(
            `${API}/reports/student/download?student_id=${encodeURIComponent(studentId)}&from_date=${fromDate}&to_date=${toDate}`,
            "_blank"
        );
    }
);


// ==========================================
// HELPERS
// ==========================================

function monthName(month) {

    const names = [

        "January",
        "February",
        "March",
        "April",
        "May",
        "June",
        "July",
        "August",
        "September",
        "October",
        "November",
        "December"
    ];

    return names[month - 1];
}


function formatDateTime(
    value
) {

    if (!value) {

        return "";
    }

    const date =
        new Date(value);

    if (
        Number.isNaN(
            date.getTime()
        )
    ) {

        return value;
    }

    return date.toLocaleString();
}