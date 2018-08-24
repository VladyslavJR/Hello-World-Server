var  socket = new ReconnectingWebSocket("ws://127.0.0.1:8000/ws");
socket.reconnectInterval = 1000;
socket.maxReconnectInterval = 120000;

var message_queue = [];

var interval;

var creditentials = {};

var last_time = undefined;
var last_date = undefined;

var current_backgroung_transperency = 0.0;

socket.onopen = function (event) {
	console.log("WS is open");

	if (!creditentials.isEmpty()){

		console.log ("sent credit.");
		var auth_msg = {
			type: "register",
			name: creditentials.name,
			password: creditentials.password,
			date: Date.now()
		};

		socket.send(JSON.stringify(auth_msg));
	}

	socket.onmessage = onMessage;

	interval = setInterval(send_ping, 1000);
};

socket.onclose = function (event) {
	clearInterval(interval);

	M.toast({html: 'Server unresponsive. Awaiting response from server.', classes: 'rounded'});
};

document.getElementById("registration_form_holder").addEventListener("keyup", function (event){
	event.preventDefault();

	var checkbox = document.getElementById("action_type_chkbx");

	if (event.keyCode == 13){
		if (!document.activeElement || document.activeElement == checkbox){
			checkbox.checked = !checkbox.checked;
		}
		else{
			document.getElementById("creditentials_confirmation_btn").click();
		}
	}
});

function attempt_register(){
	var username = document.getElementById("name_input").value;
	var password = document.getElementById("password_input").value;

	if (!username){
		setFieldError(document.getElementById("name_input"), "No name entered.");
		return;
	}

	creditentials = {
		name: username,
		password: password
	};

	var msg = {
		type: (document.getElementById("action_type_chkbx").checked) ? "authenticate" : "register",
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
			add_message_to_window(msg, (msg.name == creditentials.name) ? true : false);
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
			if (!message_queue.isEmpty){
				message_queue.forEach(function(element) {
					socket.send(element);
				});
			}
			break;
		case "ping":
			var pong = {
				"type" : "pong"
			};

			socket.send(JSON.stringify(pong));
			
			break;
	}
}

function activateClient () {
	var reg_form_holder = document.getElementById("registration_form_holder");
	reg_form_holder.removeEventListener("keyup", reg_form_holder.onkeyup);

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

		var msg_str = JSON.stringify(msg);

		if (socket.readyState == WebSocket.OPEN){
			socket.send(msg_str);
		}
		else{
			message_queue.push(msg_str);
		}

		add_message_to_window(msg, true);

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
	var new_span_name = field.id + "_temp";

	if (document.getElementById(new_span_name) != null){
		var old_span = document.getElementById(new_span_name);
		old_span.parentNode.removeChild(old_span);
	}

	var new_span = document.createElement("SPAN");
	new_span.id = new_span_name;
	var text_message = document.createTextNode(message);
	new_span.style.color = "red";
	new_span.classList.add("helper-text");

	new_span.appendChild(text_message);
	field.parentNode.appendChild(new_span);

	field.onfocus = function (event) {
		if (new_span != null && new_span.parentNode != null){
			new_span.parentNode.removeChild(new_span);
		}
		field.removeEventListener("focus", field.onfocus);
	};
}

function send_ping () {
	var ping_message = {
		"type" : "ping"
	};

	socket.send(JSON.stringify(ping_message));
}

function add_message_to_window (msg, msg_sent) {
	var msg_str = msg.text;
	var date = new Date(msg.date);

	var time = getFormattedTime(date);

	if (last_time == time)
		time = '';
	else
		last_time = time;

	var wrapper = document.createElement("div");
	wrapper.classList.add("speech-bubble");
	wrapper.classList.add("chat-container");

	var container = document.createElement("div");
	container.classList.add("message-container");

	var msg_box = document.createElement("div");

	var name_p = document.createElement("p");
	name_p.innerHTML = ((msg.name == undefined) ? creditentials.name : msg.name);
	name_p.style.color = "darkgreen";

	msg_str = escape(msg_str);

	var text_p = document.createElement("p");
	text_p.innerHTML = msg_str;

	name_p.classList.add("message-paragraph");
	text_p.classList.add("message-paragraph");

	var time_box = document.createElement("div");
	time_box.classList.add("time");

	msg_box.appendChild(name_p);
	msg_box.appendChild(text_p);

	container.appendChild(msg_box);
	container.appendChild(time_box);

	wrapper.appendChild(container);

	time_box.innerHTML = time;

	if (msg_sent){
		wrapper.classList.add("sent");
	}
	else{
		wrapper.classList.add("received");
	}

	if (time != "")
		container.style.paddingBottom = "1em";

	var chat_window = document.getElementById("chat_window");

	chat_window.appendChild(wrapper);

	chat_window.scrollTo(0, chat_window.scrollHeight);	
}

// List of HTML entities for escaping.
var escapeMap = {
    '&': '&amp;',
    '<': '&lt;',
    '>': '&gt;',
    '"': '&quot;',
    "'": '&#x27;',
    '`': '&#x60;'
};

// Functions for escaping strings to/from HTML interpolation.
// Taken from underscore.js
var createEscaper = function(map) {
	var escaper = function(match) {
		return map[match];
	};
	// Regexes for identifying a key that needs to be escaped.
	var source = '(?:' + Object.keys(map).join('|') + ')';
	var testRegexp = RegExp(source);
	var replaceRegexp = RegExp(source, 'g');
	return function(string) {
		string = string == null ? '' : '' + string;
		return testRegexp.test(string) ? string.replace(replaceRegexp, escaper) : string;
	};
};

var escape = createEscaper(escapeMap);

Object.prototype.isEmpty = function() {
		for (var key in this){
			if (this.hasOwnProperty(key))
				return false;
		}

		return true;
}

function getFormattedTime (date) {
	var minutes = String(date.getMinutes());
	var hours = String(date.getHours());

	minutes = (minutes.length == 1) ? '0' + minutes : minutes;
	hours = (hours.length == 1) ? '0' + hours : hours;

	console.log(minutes + ' ' +hours);

	return hours + ':' + minutes;
}
