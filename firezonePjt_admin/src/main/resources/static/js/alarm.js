// 경보 소리 공통 기능
// - nav의 '경보 소리 켜기' 버튼 (관제 권한 CONTROL, MASTER에게만 표시)
// - 켜고 끈 상태는 브라우저에 저장되어 다른 화면으로 이동해도 유지됨
// - 관제 화면은 dashboard.js가 새 탐지 때 FirezoneAlarm.play()를 호출
// - 그 밖의 화면은 이 파일이 5초마다 최신 탐지를 확인해 새 탐지가 있으면 소리를 냄
(function () {
    const STORAGE_KEY = 'firezone.alarmSound';
    const POLL_MS = 5000;               // 새 탐지 확인 주기 (관제 화면 외)

    const ALARM_REPEAT = 4;             // 울리는 횟수
    const ALARM_TONE_SEC = 0.7;         // 한 번 울리는 길이 (초)
    const ALARM_GAP_SEC = 0.3;          // 소리 사이 쉬는 시간 (초)
    const ALARM_FREQ = 880;             // 음 높이 (Hz)
    const ALARM_VOLUME = 0.3;           // 음량 (0 ~ 1)

    let soundOn = false;
    let audioContext = null;

    // 저장된 켜짐/꺼짐 상태 (저장소를 못 쓰는 환경이면 꺼짐으로 시작)
    function loadSaved() {
        try {
            return window.localStorage.getItem(STORAGE_KEY) === 'on';
        } catch (error) {
            return false;
        }
    }

    function save(on) {
        try {
            window.localStorage.setItem(STORAGE_KEY, on ? 'on' : 'off');
        } catch (error) {
            // 저장하지 못해도 현재 화면에서는 동작
        }
    }

    // 브라우저 정책상 사용자가 한 번 클릭·키 입력을 해야 소리를 낼 수 있음
    function ensureAudio() {
        if (!audioContext) {
            const AudioCtx = window.AudioContext || window.webkitAudioContext;
            if (!AudioCtx) {
                return null;
            }
            audioContext = new AudioCtx();
        }
        if (audioContext.state === 'suspended') {
            audioContext.resume();
        }
        return audioContext;
    }

    function play() {
        if (!soundOn || !audioContext || audioContext.state !== 'running') {
            return;
        }

        const now = audioContext.currentTime;

        for (let i = 0; i < ALARM_REPEAT; i++) {
            const start = now + i * (ALARM_TONE_SEC + ALARM_GAP_SEC);
            const end = start + ALARM_TONE_SEC;

            const tone = audioContext.createOscillator();
            const gain = audioContext.createGain();

            tone.type = 'sawtooth';
            tone.frequency.value = ALARM_FREQ;

            // 시작·끝을 부드럽게 (뚝 끊기는 잡음 방지)
            gain.gain.setValueAtTime(0, start);
            gain.gain.linearRampToValueAtTime(ALARM_VOLUME, start + 0.05);
            gain.gain.setValueAtTime(ALARM_VOLUME, end - 0.1);
            gain.gain.linearRampToValueAtTime(0, end);

            tone.connect(gain);
            gain.connect(audioContext.destination);

            tone.start(start);
            tone.stop(end);
        }
    }

    // 관제 화면(dashboard.js)에서 사용
    window.FirezoneAlarm = {
        play: play,
        isOn: function () {
            return soundOn;
        }
    };

    function updateButton(button) {
        button.textContent = soundOn ? '경보 소리 끄기' : '경보 소리 켜기';
        button.setAttribute('aria-pressed', soundOn ? 'true' : 'false');
    }

    // 관제 화면이 아닌 곳에서 새 탐지 확인
    function startPolling() {
        let lastDlNo = null;
        let timer = null;

        async function check() {
            try {
                const response = await fetch(
                    '/detections/list?page=1&size=10&direction=desc',
                    { headers: { 'Accept': 'application/json' }, cache: 'no-store' }
                );

                // 로그아웃, 권한 없음 등 -> 확인 중단
                if (!response.ok || response.redirected) {
                    window.clearInterval(timer);
                    return;
                }

                const page = await response.json();
                const list = Array.isArray(page.content) ? page.content : [];
                const newest = list.reduce(
                    (max, dto) => Math.max(max, Number(dto.dl_no) || 0), 0);

                // 처음 확인한 값은 기준으로만 저장
                if (lastDlNo === null) {
                    lastDlNo = newest;
                    return;
                }

                if (newest > lastDlNo) {
                    lastDlNo = newest;
                    play();
                }
            } catch (error) {
                // 응답이 JSON이 아니면(로그인 화면 등) 확인 중단
                window.clearInterval(timer);
            }
        }

        check();
        timer = window.setInterval(check, POLL_MS);
    }

    document.addEventListener('DOMContentLoaded', function () {
        const button = document.getElementById('alarm_sound_btn');
        if (!button) {
            return;
        }

        soundOn = loadSaved();
        updateButton(button);

        // 다른 화면에서 켜 둔 상태로 들어온 경우: 화면을 처음 누르는 순간 소리 준비
        if (soundOn) {
            const unlock = function () {
                ensureAudio();
                document.removeEventListener('pointerdown', unlock);
                document.removeEventListener('keydown', unlock);
            };
            document.addEventListener('pointerdown', unlock);
            document.addEventListener('keydown', unlock);
        }

        button.addEventListener('click', function () {
            ensureAudio();
            soundOn = !soundOn;
            save(soundOn);
            updateButton(button);

            // 켤 때 시험으로 한 번 울림 (소리 준비가 끝난 뒤)
            if (soundOn && audioContext) {
                audioContext.resume().then(play);
            }
        });

        // 관제 화면은 dashboard.js가 경보를 처리하므로 여기서는 확인하지 않음
        if (!document.getElementById('alarm_popup_area')) {
            startPolling();
        }
    });
})();
