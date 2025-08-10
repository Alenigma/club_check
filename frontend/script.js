
document.addEventListener('DOMContentLoaded', () => {
    const API_URL = 'http://localhost:8000/api';

    const getToken = () => localStorage.getItem('token');
    const setToken = (t) => localStorage.setItem('token', t);

    const parseJwt = (token) => {
        try {
            const base64Url = token.split('.')[1];
            const base64 = base64Url.replace(/-/g, '+').replace(/_/g, '/');
            const jsonPayload = decodeURIComponent(atob(base64).split('').map(function(c) {
                return '%' + ('00' + c.charCodeAt(0).toString(16)).slice(-2);
            }).join(''));
            return JSON.parse(jsonPayload);
        } catch (_) {
            return null;
        }
    };

    const enforceLogin = (nextPage) => {
        if (!getToken()) {
            window.location.href = `login.html?next=${encodeURIComponent(nextPage)}`;
            return false;
        }
        return true;
    };

    const apiFetch = async (url, options = {}) => {
        const headers = options.headers ? { ...options.headers } : {};
        const token = getToken();
        if (token) headers['Authorization'] = `Bearer ${token}`;
        return fetch(url, { ...options, headers });
    };

    // --- Student Page Logic ---
    if (document.getElementById('qr-code')) {
        if (!enforceLogin('student.html')) return;
        const payload = parseJwt(getToken());
        const currentUserId = payload?.uid;
        const qrCodeDiv = document.getElementById('qr-code');
        const studentId = currentUserId || 0;
        let selectedSectionId = null;

        const generateQrCode = (token) => {
            qrCodeDiv.innerHTML = '';
            const qr = qrcode(0, 'L');
            qr.addData(token);
            qr.make();
            qrCodeDiv.innerHTML = qr.createImgTag(8);
        };

        const attendanceEl = document.getElementById('attendance-count');
        const updateAttendanceCount = async () => {
            try {
                const url = selectedSectionId ? `${API_URL}/attendance/count?section_id=${selectedSectionId}` : `${API_URL}/attendance/count`;
                const res = await apiFetch(url);
                const data = await res.json();
                if (res.ok) {
                    if (selectedSectionId) {
                        attendanceEl.textContent = `Посещений в секции: ${data.count}`;
                    } else {
                        attendanceEl.textContent = `Посещений: ${data.count}`;
                    }
                } else {
                    attendanceEl.textContent = 'Посещений: —';
                }
            } catch (e) {
                attendanceEl.textContent = 'Посещений: —';
            }
        };

        const fetchQrToken = async () => {
            try {
                const response = await apiFetch(`${API_URL}/student/qr-token/${studentId}`);
                const data = await response.json();
                if (response.ok) {
                    generateQrCode(data.token);
                } else {
                    throw new Error(data.detail || 'Не удалось получить QR-токен');
                }
            } catch (error) {
                console.error('Ошибка получения QR-токена:', error);
                qrCodeDiv.innerHTML = 'Ошибка загрузки QR-кода.';
            }
        };

        fetchQrToken();
        setInterval(fetchQrToken, 30000);
        updateAttendanceCount();

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
                    if (!selectedSectionId) {
                        alert('Сначала выберите секцию.');
                        return;
                    }
                    // Optional Web Bluetooth discovery to prove presence
                    let beaconId = null;
                    if (navigator.bluetooth) {
                        try {
                            const device = await navigator.bluetooth.requestDevice({
                                acceptAllDevices: true,
                                optionalServices: []
                            });
                            beaconId = device?.id || device?.name || null;
                        } catch (e) {
                            // User cancelled or BLE not available; continue without beacon
                        }
                    }

                    const url = new URL(`${API_URL}/attendance/scan-lecture`);
                    url.searchParams.set('secret', decodedText);
                    url.searchParams.set('student_id', String(studentId));
                    url.searchParams.set('section_id', String(selectedSectionId));
                    if (beaconId) url.searchParams.set('beacon_id', beaconId);

                    const response = await apiFetch(url.toString(), {
                        method: 'POST'
                    });
                    const data = await response.json();
                    if (response.ok) {
                        alert(data.message || 'Отмечено.');
                        updateAttendanceCount();
                    } else {
                        alert(data.detail || 'Ошибка.');
                    }
                } catch (error) {
                    alert('Не удалось отметить посещение.');
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
                            console.error("Не удалось запустить сканер студента", err);
                            studentQrReaderDiv.innerHTML = `<strong>Ошибка:</strong> ${err}`;
                        });
                } else {
                    studentQrReaderDiv.innerHTML = "<strong>Ошибка:</strong> Камеры не найдены.";
                }
            }).catch(err => {
                studentQrReaderDiv.innerHTML = `<strong>Ошибка:</strong> Нет доступа к камере. ${err}`;
            });
        });

        // Изменение секции обновляет счётчик
        const sectionSelect = document.getElementById('section-select');
        if (sectionSelect) {
            sectionSelect.addEventListener('change', (e) => {
                selectedSectionId = parseInt(e.target.value || '0') || null;
                updateAttendanceCount();
            });
        }
    }

    // --- Teacher Page Logic ---
    if (document.getElementById('qr-reader')) {
        if (!enforceLogin('teacher.html')) return;
        let selectedSectionId = null;

        const syncOfflineScans = async () => {
            const offlineScans = JSON.parse(localStorage.getItem('offlineScans') || '[]');
            if (navigator.onLine && offlineScans.length > 0) {
                console.log(`Синхронизация ${offlineScans.length} офлайн-сканов...`);
                const promises = offlineScans.map(item => 
                    apiFetch(`${API_URL}/attendance/scan-student?token=${encodeURIComponent(item.token)}&section_id=${item.section_id}`, { method: 'POST' })
                );

                try {
                    const results = await Promise.all(promises);
                    if (results.every(res => res.ok)) {
                        localStorage.removeItem('offlineScans');
                        alert(`Успешно синхронизировано: ${offlineScans.length}.`);
                    } else {
                        alert('Некоторые офлайн-сканы не удалось отправить. Попробуйте позже.');
                    }
                } catch (error) {
                    console.error('Ошибка синхронизации:', error);
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
                if (!selectedSectionId) {
                    alert('Сначала выберите секцию.');
                    return;
                }
                const response = await apiFetch(`${API_URL}/attendance/scan-student?token=${decodedText}&section_id=${selectedSectionId}`, { method: 'POST' });
                if (!response.ok) throw new Error('Сервер ответил ошибкой');
                const data = await response.json();
                alert('Скан обработан.');
            } catch (error) {
                console.warn('Сбой сканирования, сохраняю в офлайн-очередь.', error);
                const offlineScans = JSON.parse(localStorage.getItem('offlineScans') || '[]');
                offlineScans.push({ token: decodedText, section_id: selectedSectionId });
                localStorage.setItem('offlineScans', JSON.stringify(offlineScans));
                alert('Ошибка сети. Скан сохранён локально.');
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
                const response = await apiFetch(`${API_URL}/users/`);
                const students = await response.json();
                studentListDiv.innerHTML = '';
                students.filter(s => s.role === 'student').forEach(student => {
                    const studentEl = document.createElement('div');
                    studentEl.className = 'student-item';
                    studentEl.innerHTML = `<span>${student.full_name} (ID: ${student.id})</span><button data-id="${student.id}">Отметить</button>`;
                    studentListDiv.appendChild(studentEl);
                });
            } catch (error) {
                studentListDiv.innerHTML = 'Не удалось загрузить студентов.';
            }
        };

        studentListDiv.addEventListener('click', async (e) => {
            if (e.target.tagName === 'BUTTON') {
                const studentId = e.target.dataset.id;
                try {
                    if (!selectedSectionId) {
                        alert('Сначала выберите секцию.');
                        return;
                    }
                    const response = await apiFetch(`${API_URL}/attendance/manual`, {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({ student_id: parseInt(studentId), section_id: selectedSectionId })
                    });
                    if (response.ok) {
                        alert(`Студент ${studentId} отмечен.`);
                        e.target.disabled = true;
                        e.target.textContent = 'Отмечено';
                    } else {
                        throw new Error('Не удалось отметить посещение');
                    }
                } catch (error) {
                    alert('Ошибка при отметке посещения.');
                }
            }
        });

        fetchStudents();

        // --- Master QR Mode --- 
        const enableMasterQrBtn = document.getElementById('enable-master-qr');
        const disableMasterQrBtn = document.getElementById('disable-master-qr');
        const masterQrDisplay = document.getElementById('master-qr-display');
        const masterQrCodeDiv = document.getElementById('master-qr-code');
        const teacherIdInput = document.getElementById('teacher-id-input');
        const teacherPayload = parseJwt(getToken());
        if (teacherPayload?.uid) {
            teacherIdInput.value = teacherPayload.uid;
        }

        enableMasterQrBtn.addEventListener('click', async () => {
            try {
                const teacherId = parseInt(teacherIdInput.value || '0');
                if (!teacherId) { alert('Введите ваш ID преподавателя'); return; }
                const response = await apiFetch(`${API_URL}/teacher/master-qr/enable/${teacherId}`, { method: 'POST' });
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
                    throw new Error(data.detail || 'Не удалось включить режим');
                }
            } catch (error) {
                alert(error.message);
            }
        });

        disableMasterQrBtn.addEventListener('click', async () => {
            try {
                const teacherId = parseInt(teacherIdInput.value || '0');
                if (!teacherId) { alert('Введите ваш ID преподавателя'); return; }
                const response = await apiFetch(`${API_URL}/teacher/master-qr/disable/${teacherId}`, { method: 'POST' });
                if (response.ok) {
                    masterQrDisplay.style.display = 'none';
                    enableMasterQrBtn.style.display = 'block';
                    masterQrCodeDiv.innerHTML = '';
                } else {
                    const data = await response.json();
                    throw new Error(data.detail || 'Не удалось выключить режим');
                }
            } catch (error) {
                alert(error.message);
            }
        });

        // --- Sections UI ---
        const sectionSelect = document.getElementById('section-select');
        const loadSections = async () => {
            try {
                const response = await apiFetch(`${API_URL}/sections`);
                const sections = await response.json();
                sectionSelect.innerHTML = '<option value="">Выберите секцию...</option>';
                sections.forEach(s => {
                    const opt = document.createElement('option');
                    opt.value = s.id;
                    opt.textContent = `${s.name} (#${s.id})`;
                    sectionSelect.appendChild(opt);
                });
                // also fill for beacon management
                const beaconSectionSelect = document.getElementById('beacon-section-select');
                if (beaconSectionSelect) {
                    beaconSectionSelect.innerHTML = '<option value="">Выберите секцию...</option>';
                    sections.forEach(s => {
                        const opt = document.createElement('option');
                        opt.value = s.id;
                        opt.textContent = `${s.name} (#${s.id})`;
                        beaconSectionSelect.appendChild(opt);
                    });
                }
            } catch (e) {
                console.error('Не удалось загрузить секции', e);
            }
        };
        if (sectionSelect) {
            sectionSelect.addEventListener('change', (e) => {
                selectedSectionId = parseInt(e.target.value || '0') || null;
            });
            loadSections();
        }

        // --- BLE beacons UI ---
        const beaconSectionSelect = document.getElementById('beacon-section-select');
        const beaconIdInput = document.getElementById('beacon-id-input');
        const addBeaconBtn = document.getElementById('add-beacon-btn');
        const beaconList = document.getElementById('beacon-list');

        const loadBeacons = async () => {
            const sid = parseInt(beaconSectionSelect?.value || '0');
            if (!sid) { beaconList.innerHTML = ''; return; }
            try {
                const res = await apiFetch(`${API_URL}/sections/${sid}/beacons`);
                const data = await res.json();
                if (!res.ok) throw new Error('Ошибка загрузки маячков');
                beaconList.innerHTML = data.map(b => `<div>• ${b.beacon_id}</div>`).join('');
            } catch (e) {
                beaconList.innerHTML = 'Не удалось загрузить маячки.';
            }
        };

        if (beaconSectionSelect) {
            beaconSectionSelect.addEventListener('change', loadBeacons);
        }

        if (addBeaconBtn) {
            addBeaconBtn.addEventListener('click', async () => {
                const sid = parseInt(beaconSectionSelect?.value || '0');
                const bid = (beaconIdInput?.value || '').trim();
                if (!sid) { alert('Выберите секцию'); return; }
                if (!bid) { alert('Введите ID маячка'); return; }
                try {
                    const res = await apiFetch(`${API_URL}/sections/${sid}/beacons`, {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({ section_id: sid, beacon_id: bid })
                    });
                    const data = await res.json();
                    if (!res.ok) throw new Error(data.detail || 'Не удалось добавить маячок');
                    beaconIdInput.value = '';
                    await loadBeacons();
                } catch (e) {
                    alert(e.message);
                }
            });
        }
    }
});

