
const API_URL = "/courses";

const form = document.getElementById("course-form");
const titleInput = document.getElementById("title");
const instructorInput = document.getElementById("instructor");
const durationInput = document.getElementById("duration");
const courseList = document.getElementById("course-list");
const message = document.getElementById("message");
const formTitle = document.getElementById("form-title");
const submitButton = document.getElementById("submit-button");
const cancelButton = document.getElementById("cancel-button");
const refreshButton = document.getElementById("refresh-button");

let editingCourseId = null;

function showMessage(text) {
    message.textContent = text;
}

function resetForm() {
    form.reset();
    editingCourseId = null;
    formTitle.textContent = "Add a course";
    submitButton.textContent = "Add course";
    cancelButton.hidden = true;
}

async function loadCourses() {
    courseList.replaceChildren();
    showMessage("Loading courses...");

    try {
        const response = await fetch(API_URL);

        if (!response.ok) {
            throw new Error("Could not load courses.");
        }

        const courses = await response.json();

        showMessage("");

        if (courses.length === 0) {
            courseList.textContent = "No courses found. Add your first course!";
            return;
        }

        for (const course of courses) {
            const card = document.createElement("article");
            card.className = "course-card";

            const details = document.createElement("div");
            const heading = document.createElement("h3");
            const instructor = document.createElement("p");
            const duration = document.createElement("p");

            heading.textContent = course.title;
            instructor.textContent = `Instructor: ${course.instructor}`;
            duration.textContent = `Duration: ${course.duration}`;

            details.append(heading, instructor, duration);

            const actions = document.createElement("div");
            actions.className = "course-actions";

            const editButton = document.createElement("button");
            editButton.type = "button";
            editButton.className = "secondary";
            editButton.textContent = "Edit";
            editButton.addEventListener("click", () => {
                startEditing(course);
            });

            const deleteButton = document.createElement("button");
            deleteButton.type = "button";
            deleteButton.textContent = "Delete";
            deleteButton.addEventListener("click", () => {
                deleteCourse(course.id);
            });

            actions.append(editButton, deleteButton);
            card.append(details, actions);
            courseList.append(card);
        }
    } catch (error) {
        showMessage(error.message);
    }
}

form.addEventListener("submit", async (event) => {
    event.preventDefault();

    const course = {
        title: titleInput.value.trim(),
        instructor: instructorInput.value.trim(),
        duration: Number(durationInput.value),
    };

    if (
        !course.title ||
        !course.instructor ||
        !Number.isInteger(course.duration) ||
        course.duration <= 0
    ) {
        showMessage("Enter valid course details.");
        return;
    }

    const isEditing = editingCourseId !== null;
    const url = isEditing
        ? `${API_URL}/${editingCourseId}`
        : API_URL;
    const method = isEditing ? "PUT" : "POST";

    try {
        const response = await fetch(url, {
            method,
            headers: {
                "Content-Type": "application/json",
            },
            body: JSON.stringify(course),
        });

        const result = await response.json();

        if (!response.ok) {
            throw new Error(
                result.detail
                    ? JSON.stringify(result.detail)
                    : "Could not save course."
            );
        }

        resetForm();
        showMessage(isEditing ? "Course updated!" : "Course created!");
        await loadCourses();
    } catch (error) {
        showMessage(error.message);
    }
});

function startEditing(course) {
    editingCourseId = course.id;
    titleInput.value = course.title;
    instructorInput.value = course.instructor;
    durationInput.value = course.duration;

    formTitle.textContent = "Edit course";
    submitButton.textContent = "Save changes";
    cancelButton.hidden = false;

    form.scrollIntoView({ behavior: "smooth", block: "start" });
}

async function deleteCourse(courseId) {
    if (!window.confirm("Are you sure you want to delete this course?")) {
        return;
    }

    try {
        const response = await fetch(`${API_URL}/${courseId}`, {
            method: "DELETE",
        });

        const result = await response.json();

        if (!response.ok) {
            throw new Error(result.detail || "Could not delete course.");
        }

        if (editingCourseId === courseId) {
            resetForm();
        }

        showMessage(result.message || "Course deleted.");
        await loadCourses();
    } catch (error) {
        showMessage(error.message);
    }
}

cancelButton.addEventListener("click", resetForm);
refreshButton.addEventListener("click", loadCourses);

loadCourses();
