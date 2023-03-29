const login_form = document.querySelector("#login");
const register_form = document.querySelector("#register")
const passwordEl = document.querySelector("#password");
const emailEl = document.querySelector("#email");
const confirm_passwordEl = document.querySelector("#confirm_password");
const cards_El = document.querySelector("#cards");
const more_menu_El = document.querySelector("#more-menu");
const add_card_EL = document.querySelector("#add-card");
const close_El = document.querySelector(".close");
const dashboard_button_El = document.querySelector("#dashboard-button");
const decks_more_btn_El = document.querySelector(".deck-more-btn");


const isSecurePassword = (password) => {
    const re = new RegExp("^(?=.*[a-z])(?=.*[A-Z])(?=.*[0-9])(?=.*[-\.!@#\$%\^&\*])(?=.{8,})");
    return re.test(password);
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
        showError(emailEl, "Please enter a valid email.");
    }
    else {
        success(emailEl);
        valid = true;
    }

    return valid;
}


function email_availability(validity, callback){
    if (validity){
        $.ajax({
        type: "POST",
        url: `/email_availability`,
        data: {email: emailEl.value},
        success: function(available) {
            if (available.available) {
                success(emailEl);
                callback(true);
            } else {
                showError(emailEl, "Email already in use.");
                callback(false);
            }
        }
    })
    }
    else {
        return validity;
    }
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
                email_availability(email_validate(), () => {});
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
        confirmed_password = password_confirm();

        let email_validity;

        email_availability(email_validate(), (availability) => {
            email_validity = availability;
            let register_validity =  password_validity && email_validity && confirmed_password;
            if (register_validity) {
                register_form.submit();
            }
        });
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


document.querySelector("#more-menu-link").addEventListener("click", function (e) {
    e.preventDefault();
    if (more_menu_El.style.display === "none"){
        more_menu_El.style.display = "block";
    }
    else {
        more_menu_El.style.display = "none";
    }
});


if (add_card_EL){
    add_card_EL.addEventListener("click", function () {
    let card = document.createElement("fieldset");
    card.classList.add("card");
    card.innerHTML = `<div class="del-card">
            <svg xmlns="http://www.w3.org/2000/svg" width="35" height="35" fill="currentColor" class="bi bi-x del-card"
                 viewBox="0 0 16 16">
              <path
                  d="M4.646 4.646a.5.5 0 0 1 .708 0L8 7.293l2.646-2.647a.5.5 0 0 1 .708.708L8.707 8l2.647 2.646a.5.5 0 0 1-.708.708L8 8.707l-2.646 2.647a.5.5 0 0 1-.708-.708L7.293 8 4.646 5.354a.5.5 0 0 1 0-.708z"/>
            </svg>
          </div>
          <div class="deck-info">
            <div class="word-def">
              <div class="word">
                <p class="bolder">Word *</p>
                <label>
                  <span><input name="word" type="text" class="field-input" placeholder="Type here"></span>
                </label>
              </div>
              <div class="def">
                <p class="bolder">Definition *</p>
                <label>
                  <span><input name="definition" type="text" class="field-input" placeholder="Type here"></span>
                </label>
              </div>
            </div>
            <div class="example">
              <p class="bolder">Example</p>
              <label>
                <span><input name="example" type="text" class="field-input" placeholder="Type here"></span>
              </label>
            </div>
          </div>`;
    cards_El.appendChild(card);
});
}


if (cards_El){
    cards_El.addEventListener("click", function (e) {
    if (e.target.classList.contains("del-card")) {
        e.target.parentElement.parentElement.remove();
    }
});
}


if (close_El){
    close_El.addEventListener("click", function () {
    document.querySelector(".modal").showModal();
})


document.querySelector("#leave-create").addEventListener("click", function (e) {
    e.preventDefault();
    window.location.href = "/";
});


document.querySelector("#stay-create").addEventListener("click", function (e) {
    e.preventDefault();
    document.querySelector(".modal").close();
});
}


if (dashboard_button_El){
    dashboard_button_El.addEventListener("click", () => {
    window.location.href = "/create_deck";
});
}


if (decks_more_btn_El){
    decks_more_btn_El.addEventListener("click", function () {
        alert("bro")
});
}