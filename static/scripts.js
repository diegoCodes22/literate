
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


const passwordEl = document.querySelector("#password");
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


const emailEl = document.querySelector("#email");
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


const confirm_passwordEl = document.querySelector("#confirm_password");
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


const register_form = document.querySelector("#register")
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


const login_form = document.querySelector("#login");
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


const more_menu_El = document.querySelector("#more-menu");
if (more_menu_El) {
    document.querySelector("#more-menu-link").addEventListener("click", function (e) {
    e.preventDefault();
    if (more_menu_El.style.display === "none"){
        more_menu_El.style.display = "block";
    }
    else {
        more_menu_El.style.display = "none";
    }
});
}


const cards_El = document.querySelectorAll("#cards");
const add_card_EL = document.querySelector("#add-card");
if (add_card_EL){
    for (let i = 0; i < cards_El.length; i++) {
            cards_El[i].addEventListener("click", function (e) {
                if (e.target.classList.contains("del-card")) {
                    e.target.parentElement.parentElement.remove();
                }
            });
        }
    add_card_EL.addEventListener("click", function () {
        let card = document.createElement("fieldset");
        card.classList.add("card");
        card.innerHTML = `<div class="del-card">
                <svg xmlns="http://www.w3.org/2000/svg" width="45" height="45" fill="currentColor" 
                  class="bi bi-x del-card" viewBox="0 0 16 16">
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
        card.addEventListener("click", function (e) {
                if (e.target.classList.contains("del-card")) {
                    e.target.parentElement.parentElement.remove();
                }
            });
        cards_El[0].appendChild(card);
    });
}


const close_create_El = document.querySelector("#close-create");
if (close_create_El){
    close_create_El.addEventListener("click", function () {
        document.querySelector(".modal").showModal();
});


document.querySelector("#leave-create").addEventListener("click", function (e) {
    e.preventDefault();
    window.location.href = "/";
});


document.querySelector("#stay-create").addEventListener("click", function (e) {
    e.preventDefault();
    document.querySelector(".modal").close();
});
}


const dashboard_button_El = document.querySelector("#dashboard-button");
if (dashboard_button_El){
    dashboard_button_El.addEventListener("click", () => {
    window.location.href = "/create_deck";
});
}

const decks_more_btn_El = document.querySelectorAll(".deck-more-btn");
if (decks_more_btn_El){
    for (let i = 0; i < decks_more_btn_El.length; i++){
        decks_more_btn_El[i].addEventListener("click", function (e) {
            e.stopPropagation();
            this.nextElementSibling.style.display = "block";
            document.querySelector("body").addEventListener("click", function () {
                decks_more_btn_El[i].nextElementSibling.style.display = "none";
            });
        });
    }

    const copy_deck_link_El = document.querySelector(".copy-deck-link");
    if (copy_deck_link_El) {
        copy_deck_link_El.addEventListener("click", function (e) {
        e.preventDefault();
        link = copy_deck_link_El.href;
        navigator.clipboard.writeText(link);
        alert("Link copied to clipboard")
    });
    }

}


const save_other_El = document.querySelectorAll("a[href='/save_other']");
if (save_other_El) {
    for (let i = 0; i < save_other_El.length; i++) {
        save_other_El[i].addEventListener("click", function (e) {
            e.preventDefault();
            $.ajax({
                url: "/save_other",
                type: "POST",
                data: {'dsh': save_other_El[i].id},
                success: function (response) {
                    save_other_El[i].innerHTML = "Saved";
                    save_other_El[i].style.backgroundColor = "slategray";
                    save_other_El[i].style.color = "white";
                    save_other_El[i].style.border = "none";
                    save_other_El[i].style.cursor = "default";
                }
            });
        });
    }
}

const dash_practice_El = document.querySelector("#dash-practice");
if (dash_practice_El) {
    let dash_practice_btn = dash_practice_El.firstElementChild;
    dash_practice_btn.addEventListener("click", function (e) {
        e.preventDefault();
        window.location.href = "/practice";
    });
}

const learn_state = document.querySelectorAll(".switch-box")
if (learn_state) {
    for (let i = 0; i < learn_state.length; i++){
        learn_state[i].addEventListener("input", () => {
           $.ajax({
               url: "/learning",
               type: "POST",
               data: {"state": learn_state[i].checked, "dsh": learn_state[i].parentElement.id}
           });
        });
    }
}



if (window.location.pathname === '/practice'){
    let practice_cards;
    window.addEventListener("load", () => {
       $.ajax({
            type: "GET",
            url: "/practice_card",
            success: function (response) {
                practice_cards = JSON.parse(response);
            },
            async: false
        });
        const practice_div = document.querySelector("#def-vocab-ex");
        let practice_type = Math.floor(Math.random() * 2)
        const practice_length = practice_cards.length-1;
        let i = 0;
        function renderPractice() {

            document.querySelector("#reveal-div").style.display = "block";
            document.querySelector("#remember-btns").style.display = "none";

            if (practice_type === 0) {
                practice_div.innerHTML = `
                  <div id="definition" class="practice-cards">
                    <fieldset>
                      <div>
                        <span>Definition</span>
                        <span class="bolder" id="definition-definition"></span>
                      </div>
                    </fieldset>
                  </div>
                  <div id="vocabulary" class="practice-cards">
                    <fieldset>
                      <div>
                        <span>Vocabulary</span>
                        <span class="bolder" id="vocabulary-vocabulary"></span>
                        <span id="vocabulary-example"></span>
                      </div>
                    </fieldset>
                  </div>`
                document.querySelector("#definition-definition").innerHTML = practice_cards[i][1];
            }
            else {
                practice_div.innerHTML = `
                  <div id="vocabulary" class="practice-cards">
                    <fieldset>
                      <div>
                        <span>Vocabulary</span>
                        <span class="bolder" id="vocabulary-vocabulary"></span>
                        <span id="vocabulary-example"></span>
                      </div>
                    </fieldset>
                  </div>
                  <div id="definition" class="practice-cards">
                    <fieldset>
                      <div>
                        <span>Definition</span>
                        <span class="bolder" id="definition-definition"></span>
                      </div>
                    </fieldset>
                  </div>`
                document.querySelector("#vocabulary-vocabulary").innerHTML = practice_cards[i][0];
                document.querySelector("#vocabulary-example").innerHTML = practice_cards[i][2];
            }
        }

        if (i===0){
            renderPractice();
        }

        document.querySelector("#reveal").addEventListener("click", () => {

           if (practice_type === 0){
                document.querySelector("#vocabulary-vocabulary").innerHTML = practice_cards[i][0];
                document.querySelector("#vocabulary-example").innerHTML = practice_cards[i][2];
           }
           else {
               document.querySelector("#definition-definition").innerHTML = practice_cards[i][1];
           }

           document.querySelector("#reveal-div").style.display = "none";
           document.querySelector("#remember-btns").style.display = "block";

            function f(){
                practice_cards[i][3] = +practice_cards[i][3];
                if (this.parentElement.id === "right-practice-btn") practice_cards[i][3]++;
                else if (this.parentElement.id === "left-practice-btn") practice_cards[i][3]--;
                practice_cards[i][3] = practice_cards[i][3].toString(10);

                if (i < practice_length){
                    document.querySelector("#right-practice-btn").firstElementChild.removeEventListener("click", f);
                    document.querySelector("#left-practice-btn").firstElementChild.removeEventListener("click", f);
                    i++;
                    renderPractice();
                }
                else {
                    $.ajax({
                        async: false,
                        url: "/practice_card",
                        type: "POST",
                        data: JSON.stringify(practice_cards),
                       success: (response) => {
                            window.location.pathname = response;
                       }
                    });
                }
            }

            document.querySelector("#left-practice-btn").firstElementChild.addEventListener("click", f);

            document.querySelector("#right-practice-btn").firstElementChild.addEventListener("click", f);
        });
    });
}
