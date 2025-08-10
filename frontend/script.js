
document.addEventListener('DOMContentLoaded', () => {
    const API_URL = 'http://localhost:8000/api';

    // --- Student Page Logic ---
    if (document.getElementById('qr-code')) {
        const qrCodeDiv = document.getElementById('qr-code');
        const studentId = 2; // Hardcoded for MVP

        const generateQrCode = (token) => {
            qrCodeDiv.innerHTML = '';
            const qr = qrcode(0, 'L');
            qr.addData(token);
            qr.make();
            qrCodeDiv.innerHTML = qr.createImgTag(8);
        };

        const fetchQrToken = async () => {
            try {
                const response = await fetch(`${API_URL}/student/qr-token/${studentId}`);
                const data = await response.json();
                if (response.ok) {
                    generateQrCode(data.token);
                } else {
                    throw new Error(data.detail || 'Failed to fetch QR token');
                }
            } catch (error) {
                console.error('Error fetching QR token:', error);
                qrCodeDiv.innerHTML = 'Error loading QR code.';
            }
        };

        fetchQrToken();
        setInterval(fetchQrToken, 30000);

        // --- Student QR Scanner ---
        const showScannerBtn = document.getElementById('show-scanner-btn');
        const scannerContainer = document.getElementById('student-scanner-container');
        const studentQrReaderDiv = document.getElementById('student-qr-reader');

        showScannerBtn.addEventListener('click', () => {
            scannerContainer.style.display = 'block';
            showScannerBtn.style.display = 'none';

            const studentScanner = new Html5Qrcode("student-qr-reader");

            const onScanSuccess = async (decodedText, decodedResult) => {
                console.log(`Scan successful: ${decodedText}`);
                try {
                    await studentScanner.stop();
                    scannerContainer.style.display = 'none';
                    showScannerBtn.style.display = 'block';
                } catch (e) { console.error("Failed to stop scanner", e); }

                try {
                    const response = await fetch(`${API_URL}/attendance/scan-lecture?secret=${decodedText}&student_id=${studentId}`, {
                        method: 'POST'
                    });
                    const data = await response.json();
                    alert(data.message || 'Error');
                } catch (error) {
                    alert('Failed to mark attendance.');
                }
            };

            const onScanFailure = (error) => {
                // required but can be empty
            };

            Html5Qrcode.getCameras().then(cameras => {
                if (cameras && cameras.length) {
                    const config = { fps: 10, qrbox: { width: 250, height: 250 } };
                    studentScanner.start(cameras[0].id, config, onScanSuccess, onScanFailure)
                        .catch(err => {
                            console.error("Failed to start student scanner", err);
                            studentQrReaderDiv.innerHTML = `<strong>Error:</strong> ${err}`;
                        });
                } else {
                    studentQrReaderDiv.innerHTML = "<strong>Error:</strong> No cameras found.";
                }
            }).catch(err => {
                studentQrReaderDiv.innerHTML = `<strong>Error:</strong> Could not get camera permissions. ${err}`;
            });
        });
    }

    // --- Teacher Page Logic ---
    if (document.getElementById('qr-reader')) {

        const syncOfflineScans = async () => {
            const offlineScans = JSON.parse(localStorage.getItem('offlineScans') || '[]');
            if (navigator.onLine && offlineScans.length > 0) {
                console.log(`Syncing ${offlineScans.length} offline scans...`);
                const promises = offlineScans.map(token => 
                    fetch(`${API_URL}/attendance/scan-student?token=${token}`, { method: 'POST' })
                );

                try {
                    const results = await Promise.all(promises);
                    // Check if all requests were successful
                    if (results.every(res => res.ok)) {
                        localStorage.removeItem('offlineScans');
                        alert(`Successfully synced ${offlineScans.length} saved scans.`);
                    } else {
                        alert('Some offline scans could not be synced. Please try again later.');
                    }
                } catch (error) {
                    console.error('Error during sync:', error);
                }
            }
        };

        // Listen for when the browser comes back online
        window.addEventListener('online', syncOfflineScans);
        // Attempt to sync on page load
        syncOfflineScans();

        // --- QR Scanner ---
        const qrReaderDiv = document.getElementById('qr-reader');
        const html5QrCode = new Html5Qrcode("qr-reader");

        const onScanSuccess = async (decodedText, decodedResult) => {
            console.log(`Scan successful: ${decodedText}`);
            
            try {
                // Always try to fetch first
                const response = await fetch(`${API_URL}/attendance/scan-student?token=${decodedText}`, { method: 'POST' });
                if (!response.ok) throw new Error('Server responded with an error');
                const data = await response.json();
                alert(data.message || 'Scan processed.');
            } catch (error) {
                // This block executes if fetch fails (e.g., no network)
                console.warn('Scan failed, saving to offline queue.', error);
                const offlineScans = JSON.parse(localStorage.getItem('offlineScans') || '[]');
                offlineScans.push(decodedText);
                localStorage.setItem('offlineScans', JSON.stringify(offlineScans));
                alert('Network error. Scan saved locally.');
            }
        };

        const onScanFailure = (error) => {};

        Html5Qrcode.getCameras().then(cameras => {
            if (cameras && cameras.length) {
                let cameraId = cameras[0].id;
                const backCamera = cameras.find(c => c.label.toLowerCase().includes('back'));
                if (backCamera) cameraId = backCamera.id;
                const config = { fps: 10, qrbox: { width: 250, height: 250 } };
                html5QrCode.start(cameraId, config, onScanSuccess, onScanFailure)
                    .catch(err => qrReaderDiv.innerHTML = `<strong>Error:</strong> ${err}`);
            } else {
                qrReaderDiv.innerHTML = "<strong>Error:</strong> No cameras found.";
            }
        }).catch(err => qrReaderDiv.innerHTML = `<strong>Error:</strong> ${err}`);

        // --- Manual Attendance ---
        const studentListDiv = document.getElementById('student-list');
        const fetchStudents = async () => {
            try {
                const response = await fetch(`${API_URL}/users/`);
                const students = await response.json();
                studentListDiv.innerHTML = '';
                students.filter(s => s.role === 'student').forEach(student => {
                    const studentEl = document.createElement('div');
                    studentEl.className = 'student-item';
                    studentEl.innerHTML = `<span>${student.full_name} (ID: ${student.id})</span><button data-id="${student.id}">Mark Present</button>`;
                    studentListDiv.appendChild(studentEl);
                });
            } catch (error) {
                studentListDiv.innerHTML = 'Failed to load students.';
            }
        };

        studentListDiv.addEventListener('click', async (e) => {
            if (e.target.tagName === 'BUTTON') {
                const studentId = e.target.dataset.id;
                try {
                    const response = await fetch(`${API_URL}/attendance/manual`, {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({ student_id: parseInt(studentId) })
                    });
                    if (response.ok) {
                        alert(`Marked student ${studentId} as present.`);
                        e.target.disabled = true;
                        e.target.textContent = 'Marked';
                    } else {
                        throw new Error('Failed to mark attendance');
                    }
                } catch (error) {
                    alert('Error marking attendance.');
                }
            }
        });

        fetchStudents();

        // --- Master QR Mode --- 
        const enableMasterQrBtn = document.getElementById('enable-master-qr');
        const disableMasterQrBtn = document.getElementById('disable-master-qr');
        const masterQrDisplay = document.getElementById('master-qr-display');
        const masterQrCodeDiv = document.getElementById('master-qr-code');
        const teacherId = 1; // Hardcoded for MVP

        enableMasterQrBtn.addEventListener('click', async () => {
            try {
                const response = await fetch(`${API_URL}/teacher/master-qr/enable/${teacherId}`, { method: 'POST' });
                const data = await response.json();
                if (response.ok) {
                    masterQrCodeDiv.innerHTML = '';
                    const qr = qrcode(0, 'L');
                    qr.addData(data.master_qr_secret);
                    qr.make();
                    masterQrCodeDiv.innerHTML = qr.createImgTag(8);

                    masterQrDisplay.style.display = 'block';
                    enableMasterQrBtn.style.display = 'none';
                } else {
                    throw new Error(data.detail || 'Failed to enable mode');
                }
            } catch (error) {
                alert(error.message);
            }
        });

        disableMasterQrBtn.addEventListener('click', async () => {
            try {
                const response = await fetch(`${API_URL}/teacher/master-qr/disable/${teacherId}`, { method: 'POST' });
                if (response.ok) {
                    masterQrDisplay.style.display = 'none';
                    enableMasterQrBtn.style.display = 'block';
                    masterQrCodeDiv.innerHTML = '';
                } else {
                    const data = await response.json();
                    throw new Error(data.detail || 'Failed to disable mode');
                }
            } catch (error) {
                alert(error.message);
            }
        });
    }
});
