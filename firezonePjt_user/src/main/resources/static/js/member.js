// 회원가입 유효성 검사
function signupForm() {
    console.log('signupForm() CALLED!!');

    let form = document.signup_form;

    if (form.um_id.value === '') {
        alert('INPUT NEW MEMBER ID!!');
        form.um_id.focus();

    } else if (form.um_pw.value === '') {
        alert('INPUT NEW MEMBER PW!!');
        form.um_pw.focus();

    } else if (form.um_name.value === '') {
        alert('INPUT NEW MEMBER NAME!!');
        form.um_name.focus();

    } else if (form.um_mail.value === '') {
        alert('INPUT NEW MEMBER MAIL!!');
        form.um_mail.focus();

    } else if (form.um_phone.value === '') {
        alert('INPUT NEW MEMBER PHONE!!');
        form.um_phone.focus();

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