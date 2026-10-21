// 회원가입 유효성 검사
function signupForm() {
    console.log('signupForm() CALLED!!');

    let form = document.signup_form;

    // 1. 아이디: 영문, 숫자, -, _, . 허용 / 5~19자
    // 영문과 숫자를 각각 최소 1개 포함
    const idRegex = /^(?=.*[a-zA-Z])(?=.*[0-9])[a-zA-Z0-9._-]{5,19}$/;

    // 2. 비밀번호: 영문, 숫자, -, _, . 허용 / 5~19자
    // 영문과 숫자를 각각 최소 1개 포함
    const pwRegex = /^(?=.*[a-zA-Z])(?=.*[0-9])[a-zA-Z0-9._-]{5,19}$/;

    // 3. 이름: 한글 또는 영문만 / 2~19자
    const nameRegex = /^[a-zA-Z가-힣]{2,19}$/;

    // 4. 연락처: 010-123-4567 또는 010-1234-5678 형식
    const phoneRegex = /^\d{3}-\d{3,4}-\d{4}$/;

    // 5. 이메일: 아이디 부분은 영문, 숫자, -, _, . 허용
    // @는 정확히 1개, 도메인은 영문과 마침표만 허용
    const mailRegex = /^[a-zA-Z0-9._-]+@[a-zA-Z]+\.[a-zA-Z.]+$/;

    if (form.um_id.value === '') {
        alert('INPUT NEW MEMBER ID!!');
        form.um_id.focus();
        return false;

    } else if (!idRegex.test(form.um_id.value)) {
        alert('아이디는 5~19자의 영문과 숫자를 포함해야 하며, -, _, .만 추가로 사용할 수 있습니다.');
        form.um_id.focus();
        return false;

    } else if (form.um_pw.value === '') {
        alert('INPUT NEW MEMBER PW!!');
        form.um_pw.focus();
        return false;

    } else if (!pwRegex.test(form.um_pw.value)) {
        alert('비밀번호는 5~19자의 영문과 숫자를 포함해야 하며, -, _, .만 추가로 사용할 수 있습니다.');
        form.um_pw.focus();
        return false;

    } else if (form.um_name.value === '') {
        alert('INPUT NEW MEMBER NAME!!');
        form.um_name.focus();
        return false;

    } else if (!nameRegex.test(form.um_name.value)) {
        alert('이름은 한글 또는 영문으로 2~19자 입력해주세요.');
        form.um_name.focus();
        return false;

    } else if (form.um_phone.value === '') {
        alert('INPUT NEW MEMBER PHONE!!');
        form.um_phone.focus();
        return false;

    } else if (!phoneRegex.test(form.um_phone.value)) {
        alert('연락처는 010-123-4567 또는 010-1234-5678 형식으로 입력해주세요.');
        form.um_phone.focus();
        return false;

    } else if (form.um_mail.value === '') {
        alert('INPUT NEW MEMBER MAIL!!');
        form.um_mail.focus();
        return false;

    } else if (!mailRegex.test(form.um_mail.value)) {
        alert('이메일 형식을 확인해주세요. (예: member01@example.com)');
        form.um_mail.focus();
        return false;

    } else {
        form.submit();
    }
}

function signinForm() {
    console.log('signinForm() CALLED!!');

    let form = document.signin_form;

    if (form.um_id.value === '') {
        alert('INPUT MEMBER ID!!');
        form.um_id.focus();

    } else if (form.um_pw.value === '') {
        alert('INPUT MEMBER PW!!');
        form.um_pw.focus();

    } else {
        form.submit();

    }

}


// 정보 수정 데이터 유효성 검사
function modifyForm() {
    console.log('modifyForm() CALLED!!');

    let form = document.modify_form;

    if (form.um_name.value === '') {
        alert('INPUT MEMBER NAME!!');
        form.um_name.focus();
    } else if (form.um_mail.value === '') {
        alert('INPUT MEMBER MAIL!!');
        form.um_mail.focus();
    } else if (form.um_phone.value === '') {
        alert('INPUT MEMBER PHONE!!');
        form.um_phone.focus();
    } else {
        form.submit();

    }

}

// 비밀번호 찾기 데이터 유효성 검사
function findpasswordForm() {
    console.log('findpasswordForm()');

    let form = document.findpassword_form;
    if (form.um_id.value === '') {
        alert('INPUT MEMBER ID!!')
        form.um_id.focus();

    } else if (form.um_mail.value === '') {
        alert('INPUT MEMBER MAIL!!')
        form.um_mail.focus();

    } else {
        form.submit();

    }

}