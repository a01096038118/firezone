// 회원가입 유효성 검사
function signupForm() {
    console.log('signupForm() CALLED!!');

    let form = document.signup_form;

    if (form.id.value === '') {
        alert('INPUT NEW MEMBER ID!!');
        form.id.focus();

    } else if (form.pw.value === '') {
        alert('INPUT NEW MEMBER PW!!');
        form.pw.focus();

    } else if (form.mail.value === '') {
        alert('INPUT NEW MEMBER MAIL!!');
        form.mail.focus();

    } else if (form.phone.value === '') {
        alert('INPUT NEW MEMBER PHONE!!');
        form.phone.focus();

    } else {
        form.submit();

    }

}

function signinForm() {
    console.log('signinForm() CALLED!!');

    let form = document.signin_form;

    if (form.id.value === '') {
        alert('INPUT MEMBER ID!!');
        form.id.focus();

    } else if (form.pw.value === '') {
        alert('INPUT MEMBER PW!!');
        form.pw.focus();

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
    if (form.id.value === '') {
        alert('INPUT MEMBER ID!!')
        form.id.focus();

    } else if (form.mail.value === '') {
        alert('INPUT MEMBER MAIL!!')
        form.mail.focus();

    } else {
        form.submit();

    }

}