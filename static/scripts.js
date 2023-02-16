const login_form = document.querySelector("#login");
const register_form = document.querySelector("#register")
const passwordEl = document.querySelector("#password");
const emailEl = document.querySelector("#email");
const confirm_passwordEl = document.querySelector("#confirm_password");
const form_button = document.querySelector("#form_button");

const isBetween = (length, min, max) => length > min && length < max;

const isSecurePassword = (password) => {
    const re = new RegExp("^(?=.*[a-z])(?=.*[A-Z])(?=.*[0-9])(?=.*[-\.!@#\$%\^&\*])(?=.{8,})");
    return re.test(password);
}

const isAlphaNum = (str) => {
    const re = new RegExp("^[a-zA-Z0-9]+$");
    return re.test(str);
}

const isValidEmail = (email) => {
    const re = /^(([^<>()\[\]\\.,;:\s@"]+(\.[^<>()\[\]\\.,;:\s@"]+)*)|(".+"))@((\[[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}])|(([a-zA-Z\-0-9]+\.)+[a-zA-Z]{2,}))$/;
    return re.test(email);
}

const showError = (input, error_message) => {
    const field = input.parentElement;

    field.classList.remove("success");
    field.classList.add("error");

    field.querySelector("small").textContent = error_message;
}

const success = (input) => {
    const field = input.parentElement;

    field.classList.remove("error");
    field.classList.add("success");

    field.querySelector("small").textContent = '';
}

const password_validate = () => {
    let valid = false;
    let password = passwordEl.value;

    if (!isSecurePassword(password)) {
        showError(passwordEl, 'Password must have at least 8 characters, include at least 1 lowercase character, 1 uppercase character, 1 number, and optionally special characters (!#.@$%^&*');
    }
    else {
        success(passwordEl);
        valid = true;
    }
    return valid;
}

const email_validate = () => {
    let valid = false;
    const email = emailEl.value;

    if (!isValidEmail(email)) {
        showError(emailEl, "Must enter valid email.");
    }
    else {
        success(emailEl);
        valid = true;
    }
    return valid;
}

const password_confirm = () => {
    let valid = false;
    const password = passwordEl.value;
    const confirmation = confirm_passwordEl.value;

    if (password !== confirmation) {
        showError(confirm_passwordEl, "Passwords must match.");
    }
    else {
        valid = true;
        success(confirm_passwordEl);
    }
    return valid;
}

if (register_form){
    register_form.addEventListener("input", function (e){
        e.preventDefault();

        switch (e.target.id){
            case "email":
                email_validate();
                break;
            case "password":
                password_validate();
                break;
            case "confirm_password":
                password_confirm();
                break;
        }
    });

    register_form.addEventListener("submit", function (e){
        e.preventDefault();
        let password_validity = password_validate(),
        email_validity = email_validate(),
        confirmed_password = password_confirm();

        let register_validity =  password_validity && email_validity && confirmed_password;
        // if (register_validity) {
        //     register_form.submit();
        //}

        //--Esto es el instant email check, vamos a ver si funciona lo tengo que probar despues pq me estoy quedando sin pila!!!!!!!
        if (email_validity) {
            $.ajax({
                type: "POST",
                url: "/check_email",
                data: email_validate().email,
                contentType: "aplication/json",
                dataType: "json",
                success: function(availability) {
                    if (!availability) {
                        showError(emailEl, "Email already in use.");
                    }
                    else if (register_validity && availability){
                        register_form.submit();
                    }
                }
            });
        }//--
    });
}

if (login_form) {
    login_form.addEventListener("input", function (e) {
        e.preventDefault();

        switch (e.target.id) {
            case "email":
                email_validate();
                break;
            case "password":
                password_validate();
                break;
        }
    });

    login_form.addEventListener("submit", function (e) {
        e.preventDefault();

        let username_validity = email_validate(),
            password_validity = password_validate();

        let login_validity = username_validity && password_validity;
        if (login_validity) {
            login_form.submit();
        }
    });
}
