// 회원가입 유효성 검사
function signupForm() {
    console.log('signupForm() CALLED!!');

    let form = document.signup_form;

    if (form.am_id.value === '') {
        alert('INPUT NEW ADMIN ID!!');
        form.am_id.focus();

    } else if (form.am_pw.value === '') {
        alert('INPUT NEW ADMIN PW!!');
        form.am_pw.focus();

    } else if (form.am_name.value === '') {
        alert('INPUT NEW ADMIN NAME!!');
        form.am_name.focus();

    } else if (form.am_mail.value === '') {
        alert('INPUT NEW ADMIN MAIL!!');
        form.am_mail.focus();

    } else if (form.am_phone.value === '') {
        alert('INPUT NEW ADMIN PHONE!!');
        form.am_phone.focus();

    } else {
        form.submit();

    }

}

function signinForm() {
    console.log('signinForm() CALLED!!');

    let form = document.signin_form;

    if (form.am_id.value === '') {
        alert('INPUT ADMIN ID!!');
        form.am_id.focus();

    } else if (form.am_pw.value === '') {
        alert('INPUT ADMIN PW!!');
        form.am_pw.focus();

    } else {
        form.submit();

    }

}


// 정보 수정 데이터 유효성 검사
function modifyForm() {
    console.log('modifyForm() CALLED!!');

    let form = document.modify_form;

    if (form.pw.value === '') {
        alert('INPUT MEMBER PW!!');
        form.pw.focus();

    } else if (form.mail.value === '') {
        alert('INPUT MEMBER MAIL!!');
        form.mail.focus();

    } else if (form.phone.value === '') {
        alert('INPUT MEMBER PHONE!!');
        form.phone.focus();

    } else {
        form.submit();

    }

}

// 비밀번호 찾기 데이터 유효성 검사
function findpasswordForm() {
    console.log('findpasswordForm()');

    let form = document.findpassword_form;
    if (form.am_id.value === '') {
        alert('INPUT MEMBER ID!!')
        form.am_id.focus();

    } else if (form.am_mail.value === '') {
        alert('INPUT MEMBER MAIL!!')
        form.am_mail.focus();

    } else {
        form.submit();

    }

}