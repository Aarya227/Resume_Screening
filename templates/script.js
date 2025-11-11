// script.js

document.addEventListener('DOMContentLoaded', () => {

    // --- Data Store (Simulate backend state) ---
    const appState = {
        jdFile: null,
        resumeFiles: [],
        dummyResults: [
            { name: "Alice Johnson", score: 92, skillOverlap: "Python, NLP, spaCy", experienceMatch: "5+ yrs", rank: 1 },
            { name: "Bob Williams", score: 85, skillOverlap: "Machine Learning, TensorFlow", experienceMatch: "4 yrs", rank: 2 },
            { name: "Charlie Brown", score: 78, skillOverlap: "Data Analysis, Matplotlib", experienceMatch: "2 yrs", rank: 3 },
            { name: "Diana Prince", score: 65, skillOverlap: "SQL, Excel", experienceMatch: "7+ yrs", rank: 4 },
        ]
    };

    // --- Common Functions ---
    const goToPage = (page) => {
        window.location.href = page;
    };

    // --- Login/Signup Page Logic (login.html) ---
    if (document.getElementById('loginForm')) {
        const loginForm = document.getElementById('loginForm');
        const signupForm = document.getElementById('signupForm');
        const showSignup = document.getElementById('show-signup');
        const showLogin = document.getElementById('show-login');

        loginForm.addEventListener('submit', (e) => {
            e.preventDefault();
            // In a real app, you'd send data to a server.
            // Simulating successful login:
            alert("Login successful! Redirecting to Dashboard.");
            goToPage('dashboard.html');
        });

        if (showSignup && showLogin) {
            showSignup.addEventListener('click', (e) => {
                e.preventDefault();
                loginForm.style.display = 'none';
                signupForm.style.display = 'block';
            });

            showLogin.addEventListener('click', (e) => {
                e.preventDefault();
                signupForm.style.display = 'none';
                loginForm.style.display = 'block';
            });
        }
    }

    // --- Dashboard/Upload Page Logic (dashboard.html) ---
    if (document.getElementById('jd-file-input')) {
        const jdInput = document.getElementById('jd-file-input');
        const resumesInput = document.getElementById('resumes-file-input');
        const jdList = document.getElementById('jd-file-list');
        const resumesList = document.getElementById('resumes-file-list');
        const startBtn = document.getElementById('start-analysis-btn');
        const loadingBar = document.getElementById('loading-bar');
        const progressFill = document.getElementById('progress-fill');
        const statusText = document.getElementById('analysis-status');

        const updateUploadUI = () => {
            // Update JD List
            jdList.innerHTML = '';
            if (appState.jdFile) {
                const li = document.createElement('li');
                li.innerHTML = `
                    <span><i class="fas fa-file-alt"></i> ${appState.jdFile.name}</span>
                    <button data-type="jd">Remove</button>
                `;
                jdList.appendChild(li);
            } else {
                jdList.innerHTML = '<li style="color: var(--text-medium);">No file uploaded.</li>';
            }

            // Update Resumes List
            resumesList.innerHTML = '';
            if (appState.resumeFiles.length > 0) {
                appState.resumeFiles.forEach((file, index) => {
                    const li = document.createElement('li');
                    li.innerHTML = `
                        <span><i class="fas fa-user-tie"></i> ${file.name}</span>
                        <button data-type="resume" data-index="${index}">Remove</button>
                    `;
                    resumesList.appendChild(li);
                });
            } else {
                resumesList.innerHTML = '<li style="color: var(--text-medium);">No files uploaded.</li>';
            }

            // Enable/Disable Start Button
            startBtn.disabled = !(appState.jdFile && appState.resumeFiles.length > 0);
        };

        const handleFileChange = (input, isMultiple) => {
            const files = Array.from(input.files);
            if (!isMultiple && files.length > 0) {
                appState.jdFile = files[0];
            } else if (isMultiple) {
                appState.resumeFiles = files;
            }
            updateUploadUI();
        };
        
        // Event Listeners for File Inputs
        jdInput.addEventListener('change', () => handleFileChange(jdInput, false));
        resumesInput.addEventListener('change', () => handleFileChange(resumesInput, true));

        // Event Listeners for Upload Zones (Click)
        document.getElementById('jd-upload-zone').addEventListener('click', () => jdInput.click());
        document.getElementById('resumes-upload-zone').addEventListener('click', () => resumesInput.click());

        // Event Listeners for File Removal
        document.addEventListener('click', (e) => {
            if (e.target.tagName === 'BUTTON' && e.target.textContent === 'Remove') {
                const type = e.target.dataset.type;
                if (type === 'jd') {
                    appState.jdFile = null;
                    jdInput.value = ''; // Clear file input element
                } else if (type === 'resume') {
                    const index = parseInt(e.target.dataset.index);
                    appState.resumeFiles.splice(index, 1);
                    // Clearing multiple input is tricky, easier to manage state
                }
                updateUploadUI();
            }
        });
        
        // Start Analysis Simulation
        startBtn.addEventListener('click', () => {
            startBtn.style.display = 'none';
            loadingBar.style.display = 'block';
            statusText.style.display = 'block';
            progressFill.style.width = '0%';
            
            let progress = 0;
            const interval = setInterval(() => {
                progress += 5;
                if (progress >= 100) {
                    clearInterval(interval);
                    progressFill.style.width = '100%';
                    statusText.textContent = 'Analysis Complete! Redirecting...';
                    
                    // Simulate processing time before redirect
                    setTimeout(() => {
                        goToPage('results.html');
                    }, 500);
                    
                } else {
                    progressFill.style.width = `${progress}%`;
                    if (progress < 50) {
                        statusText.textContent = `Parsing resumes (${Math.min(progress * 2, 100)}%)...`;
                    } else {
                        statusText.textContent = `Semantic matching (${Math.min((progress - 50) * 2, 100)}%)...`;
                    }
                }
            }, 100);
        });

        updateUploadUI(); // Initial UI setup
    }


    // --- Results Page Logic (results.html) ---
    if (document.getElementById('resultsTableBody')) {
        const tbody = document.getElementById('resultsTableBody');

        appState.dummyResults.forEach((data, index) => {
            const row = tbody.insertRow();
            
            // Determine highlight class
            let rankClass = '';
            if (data.rank === 1) rankClass = 'highlight-gold';
            else if (data.rank === 2) rankClass = 'highlight-silver';
            else if (data.rank === 3) rankClass = 'highlight-bronze';

            // Score Bar Color
            let barColor;
            if (data.score > 85) barColor = '#10B981'; // Green
            else if (data.score > 70) barColor = '#F59E0B'; // Yellow/Orange
            else barColor = '#EF4444'; // Red
            
            row.insertCell().innerHTML = `<span class="${rankClass}">#${data.rank}</span>`;
            row.insertCell().textContent = data.name;
            
            // Match Score Cell
            row.insertCell().innerHTML = `
                <div style="font-weight: 600;">${data.score}%</div>
                <div class="score-bar-container">
                    <div class="score-bar" style="width: ${data.score}%; background-color: ${barColor};"></div>
                </div>
            `;
            
            row.insertCell().textContent = data.skillOverlap;
            row.insertCell().textContent = data.experienceMatch;
        });
    }

});