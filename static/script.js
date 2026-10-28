
/*
 * Course Management Frontend
 * Backend: FastAPI
 *
 * Default API: http://127.0.0.1:8000
 */

const API_BASE_URL = "http://127.0.0.1:8000";
const API_URL = `${API_BASE_URL}/courses`;

const $ = (id) => document.getElementById(id);

let courses = [];

// Display success and error messages
function showMessage(message, type = "success") {
    const box = $("message");
    box.textContent = message;
    box.className = `message ${type}`;
    box.hidden = false;

    window.clearTimeout(showMessage.timer);
    showMessage.timer = window.setTimeout(() => {
        box.hidden = true;
    }, 6000);
}

// Escape text before inserting backend data into HTML
function escapeHTML(value) {
    return String(value ?? "").replace(/[&<>"']/g, char => ({
        "&": "&amp;",
        "<": "&lt;",
        ">": "&gt;",
        '"': "&quot;",
        "'": "&#39;"
    })[char]);
}

// Make requests to the backend
async function apiRequest(path = "", options = {}) {
    let response;

    try {
        response = await fetch(`${API_URL}${path}`, {
            ...options,
            headers: {
                ...(options.body
                    ? { "Content-Type": "application/json" }
                    : {}),
                ...options.headers
            }
        });
    } catch (error) {
        throw new Error(
            `Cannot connect to the backend at ${API_BASE_URL}. ` +
            "Cannot connect to the backend. Check that FastAPI is running"
        );
    }

    const text = await response.text();
    let data = null;

    if (text) {
        try {
            data = JSON.parse(text);
        } catch {
            data = text;
        }
    }

    if (!response.ok) {
        let detail = data?.detail;

        if (Array.isArray(detail)) {
            detail = detail.map(item => item.msg).join(", ");
        }

        throw new Error(
            typeof detail === "string"
                ? detail
                : `Request failed: HTTP ${response.status}`
        );
    }

    return data;
}

// Check the API connection indicator
function setAPIStatus(online) {
    const status = $("apiStatus");

    status.textContent = online
        ? "API Connected"
        : "API Unavailable";

    status.className = `api-badge ${online ? "online" : "offline"}`;
}

// Load all courses: GET /courses
async function loadCourses(showErrors = true) {
    try {
        const data = await apiRequest();

        if (!Array.isArray(data)) {
            throw new Error("The backend did not return a course list.");
        }

        courses = data;
        setAPIStatus(true);
        renderCourses();
        updateStatistics();

        return true;
    } catch (error) {
        setAPIStatus(false);

        $("courseTableBody").innerHTML = `
            <tr>
                <td colspan="5" class="empty">
                    ${escapeHTML(error.message)}
                </td>
            </tr>`;

        $("totalCourses").textContent = "—";
        $("totalInstructors").textContent = "—";
        $("totalDuration").textContent = "—";

        if (showErrors) {
            showMessage(error.message, "error");
        }

        return false;
    }
}

// Render the course table
function renderCourses() {
    const query = $("searchInput").value.trim().toLowerCase();

    const filtered = courses.filter(course =>
        [course.id, course.title, course.instructor, course.duration]
            .some(value =>
                String(value ?? "").toLowerCase().includes(query)
            )
    );

    $("courseCount").textContent =
        `${filtered.length} course${filtered.length === 1 ? "" : "s"}`;

    if (filtered.length === 0) {
        $("courseTableBody").innerHTML = `
            <tr>
                <td colspan="5" class="empty">
                    ${courses.length
                        ? "No courses match your search."
                        : "No courses found. Add your first course!"}
                </td>
            </tr>`;
        return;
    }

    $("courseTableBody").innerHTML = filtered.map(course => `
        <tr>
            <td>
                <span class="course-id">#${escapeHTML(course.id)}</span>
            </td>
            <td><strong>${escapeHTML(course.title)}</strong></td>
            <td>${escapeHTML(course.instructor)}</td>
            <td>${escapeHTML(course.duration)}</td>
            <td>
                <div class="actions">
                    <button class="action-btn"
                        data-action="view"
                        data-id="${escapeHTML(course.id)}">
                        View
                    </button>

                    <button class="action-btn"
                        data-action="edit"
                        data-id="${escapeHTML(course.id)}">
                        Edit
                    </button>

                    <button class="action-btn delete"
                        data-action="delete"
                        data-id="${escapeHTML(course.id)}">
                        Delete
                    </button>
                </div>
            </td>
        </tr>
    `).join("");
}

// Update dashboard statistics
function updateStatistics() {
    $("totalCourses").textContent = courses.length;

    const instructors = new Set(
        courses
            .map(course => String(course.instructor ?? "").trim().toLowerCase())
            .filter(Boolean)
    );

    $("totalInstructors").textContent = instructors.size;

    const duration = courses.reduce(
        (total, course) => total + (Number(course.duration) || 0),
        0
    );

    $("totalDuration").textContent = duration;
}

// Clear the form and return to add mode
function clearForm() {
    $("courseForm").reset();
    $("courseId").value = "";
    $("formTitle").textContent = "Add a Course";
    $("saveBtn").textContent = "Add Course";
}

// Validate a course ID
function getValidId(value) {
    const id = Number(value);
    return Number.isInteger(id) && id > 0 ? id : null;
}

// ADD and UPDATE
// POST /courses
// PUT /courses/{course_id}
$("courseForm").addEventListener("submit", async event => {
    event.preventDefault();

    const title = $("title").value.trim();
    const instructor = $("instructor").value.trim();
    const duration = Number($("duration").value);
    const courseId = getValidId($("courseId").value);

    if (!title || title.length > 150) {
        showMessage(
            "Title is required and must be at most 150 characters.",
            "error"
        );
        return;
    }

    if (!instructor || instructor.length > 100) {
        showMessage(
            "Instructor is required and must be at most 100 characters.",
            "error"
        );
        return;
    }

    if (!Number.isInteger(duration) || duration <= 0) {
        showMessage("Duration must be a positive whole number.", "error");
        return;
    }

    const courseData = {
        title: title,
        instructor: instructor,
        duration: duration
    };

    const button = $("saveBtn");
    const originalText = button.textContent;

    button.disabled = true;
    button.textContent = courseId ? "Updating..." : "Adding...";

    try {
        const result = await apiRequest(
            courseId ? `/${courseId}` : "",
            {
                method: courseId ? "PUT" : "POST",
                body: JSON.stringify(courseData)
            }
        );

        clearForm();
        await loadCourses(false);

        showMessage(
            courseId
                ? `Course #${courseId} updated successfully.`
                : `Course added successfully! ID: ${result?.id ?? "created"}`,
            "success"
        );
    } catch (error) {
        showMessage(error.message, "error");
    } finally {
        button.disabled = false;
        button.textContent = originalText;
    }
});

// VIEW COURSE BY ID: GET /courses/{course_id}
$("findForm").addEventListener("submit", async event => {
    event.preventDefault();

    const id = getValidId($("findId").value);

    if (id === null) {
        showMessage("Please enter a valid positive course ID.", "error");
        return;
    }

    $("findResult").innerHTML =
        '<div class="loading">Searching for course...</div>';

    try {
        const course = await apiRequest(`/${id}`);

        $("findResult").innerHTML = `
            <div class="result-card">
                <h3>${escapeHTML(course.title)}</h3>
                <p><strong>ID:</strong> ${escapeHTML(course.id)}</p>
                <p><strong>Instructor:</strong>
                    ${escapeHTML(course.instructor)}</p>
                <p><strong>Duration:</strong>
                    ${escapeHTML(course.duration)}</p>
                <div class="result-actions">
                    <button class="btn primary"
                        data-action="edit"
                        data-id="${escapeHTML(course.id)}">
                        Update Course
                    </button>
                    <button class="btn danger"
                        data-action="delete"
                        data-id="${escapeHTML(course.id)}">
                        Delete Course
                    </button>
                </div>
            </div>`;
    } catch (error) {
        $("findResult").innerHTML = `
            <div class="message error">${escapeHTML(error.message)}</div>`;
    }
});

// Fill the form with an existing course for editing
async function editCourse(id) {
    try {
        let course = courses.find(item => Number(item.id) === id);

        // If not in the current list, fetch it from the backend
        if (!course) {
            course = await apiRequest(`/${id}`);
        }

        $("courseId").value = course.id;
        $("title").value = course.title;
        $("instructor").value = course.instructor;
        $("duration").value = course.duration;

        $("formTitle").textContent = `Update Course #${course.id}`;
        $("saveBtn").textContent = "Save Changes";

        $("formPanel").scrollIntoView({
            behavior: "smooth",
            block: "start"
        });

        $("title").focus();
    } catch (error) {
        showMessage(error.message, "error");
    }
}

// DELETE COURSE: DELETE /courses/{course_id}
async function deleteCourse(id) {
    const confirmed = window.confirm(
        `Are you sure you want to delete course #${id}?\n\n` +
        "This action cannot be undone."
    );

    if (!confirmed) return;

    try {
        await apiRequest(`/${id}`, {
            method: "DELETE"
        });

        if (Number($("courseId").value) === id) {
            clearForm();
        }

        if (Number($("findId").value) === id) {
            $("findResult").innerHTML = "";
        }

        await loadCourses(false);

        showMessage(`Course #${id} deleted successfully.`, "success");
    } catch (error) {
        showMessage(error.message, "error");
    }
}

// Handle View, Edit and Delete buttons
document.addEventListener("click", async event => {
    const button = event.target.closest("[data-action]");

    if (!button) return;

    const id = getValidId(button.dataset.id);

    if (id === null) return;

    switch (button.dataset.action) {
        case "view":
            $("findId").value = id;
            $("findForm").requestSubmit();
            $("findForm").scrollIntoView({
                behavior: "smooth",
                block: "start"
            });
            break;

        case "edit":
            await editCourse(id);
            break;

        case "delete":
            await deleteCourse(id);
            break;
    }
});

// Search courses in the already-loaded list
$("searchInput").addEventListener("input", renderCourses);

// Refresh the list from the backend
$("refreshBtn").addEventListener("click", async () => {
    const button = $("refreshBtn");

    button.disabled = true;
    button.textContent = "Loading...";

    await loadCourses();

    button.disabled = false;
    button.textContent = "Refresh";
});

// Header Add Course button
$("showAddBtn").addEventListener("click", () => {
    clearForm();

    $("formPanel").scrollIntoView({
        behavior: "smooth",
        block: "start"
    });

    $("title").focus();
});

// Clear form
$("clearBtn").addEventListener("click", clearForm);

// Load courses when the page opens
document.addEventListener("DOMContentLoaded", () => {
    loadCourses();
});
