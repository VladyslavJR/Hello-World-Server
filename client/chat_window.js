var  socket = new WebSocket("ws://127.0.0.1:8000/ws");

socket.onopen = function (event) {
	console.log("WS is open");

	socket.onmessage = onMessage;
};

function changeLabel () {
	var cb = document.getElementById("action_type_chkbx");
	document.getElementById("action_type_label").innerHTML = (cb.checked) ? "Register" : "Log In";
}

document.getElementById("name_input").addEventListener("keyup", clickButtonOnEnter);

document.getElementById("password_input").addEventListener("keyup", clickButtonOnEnter);

function clickButtonOnEnter (event){
	event.preventDefault();

	if (event.keyCode == 13){
		document.getElementById("creditentials_confirmation_btn").click();
	}
}

function attempt_register(){
	var username = document.getElementById("name_input").value;
	var password = document.getElementById("password_input").value;

	if (!username){
		setFieldError(document.getElementById("name_input"), "No name entered.");
		return;
	}

	var msg = {
		type: (document.getElementById("action_type_chkbx").checked) ? "register" : "authenticate",
		name: username,
		password: password,
		date: Date.now()
	};

	socket.send(JSON.stringify(msg));
}

function onMessage(msg){
	var chat_window = document.getElementById("chat_window");
	var msg = JSON.parse(event.data);
	var text = "";

	switch(msg.type){
		case "message":
			text = "[" + msg.name + "] " + msg.text;
			break;
		case "regfailed":
			console.log("Reg failed.");
			switch(msg.reason){
				case "nametaken":
					setFieldError(document.getElementById("name_input"), "Name already taken.");
					var pass_field = document.getElementById("password_input");
					break;
				case "invalidpassword":
					var pass_field = document.getElementById("password_input");
					setFieldError(pass_field, "Invalid password");
					pass_field.value = "";
					break;
			}
			break;
		case "authfailed":
			switch(msg.reason){
				case "nameinuse":
					setFieldError(document.getElementById("name_input"), "Name already in use.");
					break;
				case "invalidpassword":
					setFieldError(document.getElementById("password_input"), "Invalid password.");
					break;
				case "nouser":
					setFieldError(document.getElementById("name_input"), "No user by that name.");
					break;
				case "unknown":
					setFieldError(document.getElementById("creditentials_confirmation_btn"), 
						"Unknown error.");
					break;
			}
			break;
		case "register":
			console.log("Registration successfull.");
			activateClient();
			break;
		case "authenticated":
			console.log("Log in successfull");
			activateClient();
			break;
	}

	if (text.length){
		var new_p = document.createElement("p");
		new_p.innerHTML = text;
		chat_window.appendChild(new_p);

		chat_window.scrollTo(0, chat_window.scrollHeight);
	}
}

function activateClient () {
	document.getElementById("name_input").removeEventListener("keyup", clickButtonOnEnter);
	document.getElementById("password_input").removeEventListener("keyup", clickButtonOnEnter);

	var reg_form_holder = document.getElementById("registration_form_holder");
	reg_form_holder.parentElement.removeChild(reg_form_holder);

	document.getElementById("active_chat_area").hidden = false;

	document.getElementById("textbox").autofocus = true;
	document.getElementById("textbox").focus();

	document.getElementById("send_button").onclick = function (event) {
		var textbox = document.getElementById("textbox");

		var msg = {
			type: "message",
			text: textbox.value,
			date: Date.now()
		};

		socket.send(JSON.stringify(msg));

		textbox.value = "";
	};

	document.getElementById("textbox").addEventListener("keyup", function (event) {
		event.preventDefault();

		if (event.keyCode === 13){
			document.getElementById("send_button").click();
		}
	});
}

function setFieldError (field, message) {
	var last_border = field.style.border;

	field.insertAdjacentText("afterend", message);

	field.style.border = "2px solid red";

	field.onfocus = function (event) {
		field.style.border = last_border;
		field.textContent = "";
		field.onfocus = null;
	};
}

function sendPing () {
	var ping = {
		type: "ping"
	};

	socket.send(JSON.stringify(ping));
}
