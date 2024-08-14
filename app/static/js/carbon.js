function callAjax(url, callback, elem){
    var xmlhttp;
    // compatible with IE7+, Firefox, Chrome, Opera, Safari
    xmlhttp = new XMLHttpRequest();
    xmlhttp.onreadystatechange = function(){
        if (xmlhttp.readyState == 4 && xmlhttp.status == 200){
            if (callback) {
                callback(xmlhttp.responseText, elem);
            }
        }
    }

    xmlhttp.onerror = function(){
        alert('[connection error] Не удалось проверить авторизацию клиента. Из-за проблем с сетью.')
    }

    xmlhttp.ontimeout = function(){
        alert("[timeout response] Не удалось проверить авторизацию клиента.");
    }

    xmlhttp.open("GET", url, true);
    xmlhttp.timeout = 2000;
    xmlhttp.send();
}

function openChild(iid, parent_iid) {
    document.getElementById(iid).style.display = 'block';
    document.getElementById(parent_iid).href = `javascript:closeChild('${iid}', '${parent_iid}')`;
}
function closeChild(iid, parent_iid) {
    document.getElementById(iid).style.display = 'none';
    document.getElementById(parent_iid).href = `javascript:openChild('${iid}', '${parent_iid}')`;
}

async function updateSess() {
    try {
        let pppoe = await fetch('/carbon/pppoe/all/');
        if (pppoe.ok) {
            let sessions = await pppoe.json();
            let logins = sessions['response'];
            let users = document.getElementsByClassName('users');
            for (let i=0; i < users.length; i++) {
                if (logins.includes(users[i].id)) {
                    
                    let text = users[i].textContent;
                    users[i].textContent = `-> ${text}`
                }
            }
        };
    } catch {
        alert("Не удалось получить состояния авторизации абонентов. Один из NAS (pppoe) серверов не отвечает.")
    }
        
    
}

function searchUsers(data, is_event=true) {
    let search_str = ''
    if (is_event) {
        search_str = data.target.value;
    } else {
        search_str = data;
    }
    
    let users = document.getElementsByClassName('div-users');
    let child_nodes = document.getElementsByClassName('child-folder');
    for (let i=0; i < child_nodes.length; i++) {
        child_nodes[i].style.display = 'block';
        
    }
    if (!search_str) {
        for (let i=0; i < child_nodes.length; i++) {
            child_nodes[i].style.display = 'none';  
        }
        for (let i=0; i < users.length; i++) {
            users[i].style.display = 'flex';  
        }
        return;   
    }

    for (let i=0; i < users.length; i++) {
        let name_html = users[i].textContent.toLowerCase();
        key2 = name_html.indexOf(search_str.toLowerCase());
        if (key2 == -1) {
            users[i].style.display = 'none';
        } else {
            users[i].style.display = 'flex';
        }

    }
}

function updatePppoe(response, user_elem) {
    let status = JSON.parse(response);
    let last_state = user_elem.textContent.replace('->', '');
    
    if (status['status']) {
        user_elem.textContent = `-> ${last_state}`;
        console.log(status);
    } else if (status['error']) {
        alert("Один из NAS (pppoe) серверов не отвечает. Невозможно корректно отобразить состояние абонента.")
    } else {
        user_elem.textContent = last_state;

        console.log(last_state);
        console.log(status);
    }  
    
}

let timer_open_button = '';
let select_user_elem = '';
function clickUserButton(iid, login) {
    clearTimeout(timer_open_button);
    let open_btn = document.getElementsByClassName('mini-panel')[0];
    let user_elem = document.getElementById(login);
    setTimeout(callAjax, 100, `/carbon/pppoe/one/?login=${login}`, updatePppoe, user_elem); // обновить состояние сессии
    if (select_user_elem) {
        select_user_elem.style.backgroundColor = 'white';
        select_user_elem.style.color = 'black';
    }
    user_elem.style.backgroundColor = '#0078d7';
    user_elem.style.color = 'white';
    select_user_elem = user_elem;
    open_btn.style.display = 'block';
    open_btn.href = `javascript: clickMiniPanel('${iid}')`;
    timer_open_button = setTimeout(function() {
        open_btn.style.display = 'none';
        open_btn.textContent = 'Открыть';
    }, 10000)
}

function clickMiniPanel(iid) {
    let open_btn = document.getElementsByClassName('mini-panel')[0];
    window.open('./info/?iid=' + String(iid), '_self')
    open_btn.textContent = 'Загрузка...';

}

//привязка обработчика на поле search
let search = document.getElementsByClassName('search-input')[0]
search.addEventListener('input', searchUsers);

updateSess();