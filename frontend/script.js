
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
    }

    // --- Teacher Page Logic ---
    if (document.getElementById('qr-reader')) {
        const studentListDiv = document.getElementById('student-list');

        // --- QR Scanner ---
        const qrReaderDiv = document.getElementById('qr-reader');
        const html5QrCode = new Html5Qrcode("qr-reader");

        const onScanSuccess = async (decodedText, decodedResult) => {
            console.log(`Scan successful: ${decodedText}`);
            try {
                // Stop scanning to free up the camera
                await html5QrCode.stop();
            } catch (e) {
                console.error("Failed to stop the scanner", e);
            }

            try {
                const response = await fetch(`${API_URL}/attendance/scan-student?token=${decodedText}`, {
                    method: 'POST',
                });
                const data = await response.json();
                alert(data.message || 'Error processing scan.');
            } catch (error) {
                console.error('Error sending token to server:', error);
                alert('Failed to mark attendance.');
            }
        };

        const onScanFailure = (error) => {
            // This callback is required but we can leave it empty if we don't want to log anything.
            // console.warn(`Code scan error = ${error}`);
        };

        Html5Qrcode.getCameras().then(cameras => {
            if (cameras && cameras.length) {
                let cameraId = cameras[0].id;
                const backCamera = cameras.find(c => c.label.toLowerCase().includes('back'));
                if (backCamera) {
                    cameraId = backCamera.id;
                }
                
                const config = { fps: 10, qrbox: { width: 250, height: 250 } };

                html5QrCode.start(cameraId, config, onScanSuccess, onScanFailure)
                    .catch(err => {
                        console.error("Failed to start scanner", err);
                        qrReaderDiv.innerHTML = `<strong>Error:</strong> ${err}`;
                    });
            } else {
                console.error("No cameras found.");
                qrReaderDiv.innerHTML = "<strong>Error:</strong> No cameras found on this device.";
            }
        }).catch(err => {
            console.error("Error getting camera list:", err);
            qrReaderDiv.innerHTML = "<strong>Error:</strong> Could not get camera permissions.";
        });

        // --- Manual Attendance ---
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
                console.error('Error fetching students:', error);
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
                        const data = await response.json();
                        throw new Error(data.detail || 'Failed to mark attendance');
                    }
                } catch (error) {
                    console.error('Error marking attendance:', error);
                    alert('Error marking attendance.');
                }
            }
        });

        fetchStudents();
    }
});
