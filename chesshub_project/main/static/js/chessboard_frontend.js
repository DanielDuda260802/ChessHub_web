import { Chess } from "/static/chess.js-0.13.4/chess.js"

document.addEventListener("DOMContentLoaded", function () {
    var game = new Chess();

    var board = Chessboard("board", {
        draggable: true,
        position: "start",
        pieceTheme: "/static/chessboardjs-1.0.0/img/chesspieces/wikipedia/{piece}.png",
        onDrop: onDrop
    });

    console.log("Chessboard initialized:", board); 
    window.board = board; 
    window.game = game;  

function onDrop(source, target) {
    const move = `${source}${target}`;
    const piece = board.position()[source]; 

    const isPawnPromotion =
        (piece === "wP" && target[1] === "8") || 
        (piece === "bP" && target[1] === "1");  

        if (isPawnPromotion) {
            showPromotionMenu(move, target); 
            return "snapback"; 
        } else {
            sendMoveToBackend(move); 
        }
    }

function showPromotionMenu(move, targetSquare) {
    const menu = document.createElement("div");
    menu.id = "promotion-menu";
    menu.style.position = "absolute";
    menu.style.backgroundColor = "white";
    menu.style.border = "1px solid black";
    menu.style.padding = "10px";
    menu.style.zIndex = "1000";
    menu.style.display = "flex";
    menu.style.flexDirection = "row";
    menu.style.justifyContent = "center";
    menu.style.alignItems = "center";
    
    const boardElement = document.getElementById("board");
    const boardRect = boardElement.getBoundingClientRect();
    const squareSize = boardRect.width / 8;

    console.log("Board Rect:", boardRect);
    console.log("Square Size:", squareSize);

    const col = targetSquare.charCodeAt(0) - 97;
    const row = 8 - parseInt(targetSquare[1]);

    console.log("Column:", col, "Row:", row);

    const squareCenterX = boardRect.left + col * squareSize + squareSize / 2;
    const squareCenterY = boardRect.top + row * squareSize + squareSize / 2;

    console.log("Square Center X:", squareCenterX, "Square Center Y:", squareCenterY);

    document.body.appendChild(menu);
    const menuWidth = menu.offsetWidth;
    const menuHeight = menu.offsetHeight;

    console.log("Menu Width:", menuWidth, "Menu Height:", menuHeight);

    const left = squareCenterX - menuWidth / 2;
    const top = squareCenterY - menuHeight / 2;

    console.log("Calculated Left:", left, "Calculated Top:", top);

    menu.style.left = `${left}px`;
    menu.style.top = `${top}px`;
    
    const pieces = ["q", "r", "b", "n"];
    const pieceImages = {
        "w": { "q": "wQ", "r": "wR", "b": "wB", "n": "wN" },
        "b": { "q": "bQ", "r": "bR", "b": "bB", "n": "bN" },
    };
    
    const position = board.position(); // Get current board position
    const piece = position[move.substring(0, 2)];
    const color = piece[0];

    pieces.forEach((pieceType) => {
        const button = document.createElement("button");
        button.style.border = "none";
        button.style.background = "none";
        button.style.cursor = "pointer";
        button.style.margin = "5px";
    
        const img = document.createElement("img");
        img.src = `/static/chessboardjs-1.0.0/img/chesspieces/wikipedia/${pieceImages[color][pieceType]}.png`;
        img.alt = pieceType.toUpperCase();
        img.style.width = "40px";
        img.style.height = "40px";
    
        button.appendChild(img);
        button.addEventListener("click", function () {
            document.body.removeChild(menu);
            const promotionMove = move + pieceType.toUpperCase();
            sendMoveToBackend(promotionMove);
        });
        menu.appendChild(button);
    });
    document.body.appendChild(menu);
}
    
function sendMoveToBackend(move) {
    const previousFen = board.fen();

    fetch("/add-move/", {
        method: "POST",
        headers: {
            "Content-Type": "application/json",
            "X-CSRFToken": getCsrfToken()
        },
        body: JSON.stringify({ move: move })
    })
        .then((response) => {
            if (!response.ok) {
                return response.json().then((data) => {
                    throw new Error(data.error || "Unknown error");
                });
            }
            return response.json();
        })
        .then((data) => {
            if (data.fen) {
                board.position(data.fen);
                updateButtonStates();
            }
        })
        .catch((error) => {
            console.error("Error adding move:", error.message);
            board.position(previousFen);
        });
    }

function updateButtonStates() {
    fetch("/current_state/", {
        method: "GET",
        headers: {
            "Content-Type": "application/json",
            "X-CSRFToken": getCsrfToken()
        }
    })
        .then((response) => {
            if (!response.ok) {
                throw new Error("Failed to fetch button states.");
            }
            return response.json();
        })
        .then((data) => {
            const isAtStart = data.is_at_start; 
            const hasNextMove = data.has_next_move; 

            document.getElementById("prev-move").disabled = isAtStart;
            document.getElementById("next-move").disabled = !hasNextMove;
        })
        .catch((error) => console.error("Error updating button states:", error));
}

function navigateBack() {
    fetch("/prev-move/", {
        method: "POST",
        headers: {
            "X-CSRFToken": getCsrfToken()
        }
    })
        .then((response) => {
            if (!response.ok) {
                return response.json().then((data) => {
                    throw new Error(data.error || "Unknown error");
                });
            }
            return response.json();
        })
        .then((data) => {
            if (data.fen) {
                board.position(data.fen);
            }
            updateButtonStates();
        })
        .catch((error) => {
            console.error("Error navigating back:", error.message);
        });
}

document.getElementById("prev-move").addEventListener("click", function () {
    navigateBack();
});

document.addEventListener("keydown", function (event) {
    if (event.key === "ArrowLeft") {
        navigateBack();
    }
});

function navigateNext() {
    fetch("/next-move/", {
        method: "POST",
        headers: {
            "X-CSRFToken": getCsrfToken()
        }
    })
        .then((response) => {
            if (!response.ok) {
                return response.json().then((data) => {
                    throw new Error(data.error || "Unknown error");
                });
            }
            return response.json();
        })
        .then((data) => {
            if (data.variations) {
                console.log("Dostupne varijacije:", data.variations);
                showVariationMenu(data.variations);
            } else if (data.fen) {
                board.position(data.fen);
                updateButtonStates();
            } else {
                console.error("Unexpected response:", data);
            }
        })
        .catch((error) => {
            console.error("Error navigating next:", error.message);
        });
}


document.getElementById("next-move").addEventListener("click", function () {
    navigateNext();
});

document.addEventListener("keydown", function (event) {
    if (event.key === "ArrowRight") {
        navigateNext();
    }
});

updateButtonStates();

function showVariationMenu(variations) {
    const menu = document.createElement("div");
    menu.id = "variation-menu";

    const list = document.createElement("ul");
    list.className = "variation-menu-list";

    let currentIndex = 0;

    variations.forEach((variation, index) => {
        const listItem = document.createElement("li");
        listItem.textContent = variation;
        listItem.className = "variation-menu-item";
        if (index === currentIndex) {
            listItem.classList.add("active");
        }

        listItem.addEventListener("click", function () {
            console.log("Odabrana varijacija klikom:", variation);
            closeMenu(); 
            selectVariation(index);
        });

        list.appendChild(listItem);
    });

    menu.appendChild(list);
    document.body.appendChild(menu);

    function handleKeyNavigation(event) {
        const listItems = list.querySelectorAll(".variation-menu-item");

        if (event.key === "ArrowDown") {
            currentIndex = (currentIndex + 1) % variations.length;
            updateHighlight(listItems);
        } else if (event.key === "ArrowUp") {
            currentIndex = (currentIndex - 1 + variations.length) % variations.length;
            updateHighlight(listItems);
        } else if (event.key === "Enter") {
            closeMenu(); 
            selectVariation(currentIndex);
        }
    }

    function updateHighlight(listItems) {
        listItems.forEach((item, index) => {
            item.classList.toggle("active", index === currentIndex);
        });
    }

    function closeMenu() {
        document.body.removeChild(menu);
        document.removeEventListener("keydown", handleKeyNavigation);
        console.log("Izbornik zatvoren.");
    }

    document.addEventListener("keydown", handleKeyNavigation);

    menu.focus();
}


function selectVariation(index) {
    fetch("/choose-variation/", {
        method: "POST",
        headers: {
            "Content-Type": "application/json",
            "X-CSRFToken": getCsrfToken()
        },
        body: JSON.stringify({ variation_index: index })
    })
        .then((response) => response.json())
        .then((data) => {
            if (data.fen) {
                board.position(data.fen); 
            }
            if (data.pgn) {
                updatePGN(data.pgn); 
            }
        })
        .catch((error) => console.error("Error selecting variation:", error));
}

function updatePGN(pgn) {
    document.getElementById("pgn-output").textContent = pgn;
    console.log("Updated PGN:", pgn);
}

function getCsrfToken() {
    return document.querySelector("meta[name='csrf-token']").getAttribute("content");
}
});

/* GAME LIST **/
let currentPage = 1

function showLoader(text = "Loading games...") {
    const loader = document.getElementById("loader");
    const loadingText = loader.querySelector(".loading-text");
    loadingText.textContent = text; 
    document.getElementById("loader-overlay").style.display = "block";
    loader.style.display = "block";
}

function hideLoader() {
    const loader = document.getElementById("loader");
    document.getElementById("loader-overlay").style.display = "none";
    loader.style.display = "none";
    document.body.style.pointerEvents = "auto";
}

async function fetchGames(page = 1) {
    showLoader();

    try {
        const response = await fetch(`/get_games/?page=${page}`);
        const data = await response.json();

        renderGames(data.games);
        setupPagination(data.total_pages, data.current_page);

    } catch (error) {
        console.error("Error fetching games:", error);
    } finally {
        hideLoader();
    }
}

function renderGames(games) {
    const tableBody = document.querySelector('#game-list-table tbody');
    tableBody.innerHTML = '';
    games.forEach(game => {
        const row = document.createElement('tr');
        row.innerHTML = `
            <td>${game.white_player || 'Unknown'}</td>
            <td>${game.white_elo || 'N/A'}</td>
            <td>${game.black_player || 'Unknown'}</td>
            <td>${game.black_elo || 'N/A'}</td>
            <td>${game.result || 'N/A'}</td>
            <td>${game.date || 'N/A'}</td>
            <td>${game.site || 'N/A'}</td>
        `;
        row.addEventListener('click', () => {
            const url = `/game_details/${game.id}/`; 
            console.log(`Opening game details for Game ID: ${game.id} at ${url}`);
            window.open(url, '_blank');
        });
        tableBody.appendChild(row);
    });
}

function setupPagination(totalPages, currentPage) {
    const pagination = document.querySelector('#pagination');
    pagination.innerHTML = ''; 

    console.log(`Pagination initialized: Total Pages: ${totalPages}, Current Page: ${currentPage}`);

    const nav = document.createElement('nav');
    const ul = document.createElement('ul');
    ul.classList.add('pagination');

    const maxVisiblePages = 3;
    let startPage = Math.max(1, currentPage - Math.floor(maxVisiblePages / 2));
    let endPage = Math.min(totalPages, startPage + maxVisiblePages - 1);

    if (endPage - startPage + 1 < maxVisiblePages) {
        startPage = Math.max(1, endPage - maxVisiblePages + 1);
    }

    const prevDisabled = currentPage === 1 ? 'disabled' : '';
    const prevButton = document.createElement('li');
    prevButton.className = `page-item ${prevDisabled}`;
    prevButton.innerHTML = `
        <a class="page-link" href="#" aria-label="Previous">&laquo;</a>
    `;
    prevButton.addEventListener('click', () => {
        if (currentPage > 1) fetchGames(currentPage - 1);
    });
    ul.appendChild(prevButton);

    if (startPage > 1) {
        const firstPage = document.createElement('li');
        firstPage.className = 'page-item';
        firstPage.innerHTML = `
            <a class="page-link" href="#">1</a>
        `;
        firstPage.addEventListener('click', () => fetchGames(1));
        ul.appendChild(firstPage);

        if (startPage > 2) {
            const dots = document.createElement('li');
            dots.className = 'page-item disabled';
            dots.innerHTML = `<span class="page-link">...</span>`;
            ul.appendChild(dots);
        }
    }

    for (let i = startPage; i <= endPage; i++) {
        const pageItem = document.createElement('li');
        pageItem.className = `page-item ${i === currentPage ? 'active' : ''}`;
        pageItem.innerHTML = `<a class="page-link" href="#">${i}</a>`;
        pageItem.addEventListener('click', () => fetchGames(i));
        ul.appendChild(pageItem);
    }

    if (endPage < totalPages) {
        if (endPage < totalPages - 1) {
            const dots = document.createElement('li');
            dots.className = 'page-item disabled';
            dots.innerHTML = `<span class="page-link">...</span>`;
            ul.appendChild(dots);
        }

        const lastPage = document.createElement('li');
        lastPage.className = 'page-item';
        lastPage.innerHTML = `
            <a class="page-link" href="#">${totalPages}</a>
        `;
        lastPage.addEventListener('click', () => fetchGames(totalPages));
        ul.appendChild(lastPage);
    }

    const nextDisabled = currentPage === totalPages ? 'disabled' : '';
    const nextButton = document.createElement('li');
    nextButton.className = `page-item ${nextDisabled}`;
    nextButton.innerHTML = `
        <a class="page-link" href="#" aria-label="Next">&raquo;</a>
    `;
    nextButton.addEventListener('click', () => {
        if (currentPage < totalPages) fetchGames(currentPage + 1);
    });
    ul.appendChild(nextButton);

    nav.appendChild(ul);
    pagination.appendChild(nav);
}

document.addEventListener("DOMContentLoaded", async function () {
    await fetchGames(currentPage); 
});

fetchGames(currentPage);

if (!window.socket) {
    window.socket = new WebSocket("ws://localhost:8001/ws/games/");
}

socket.onopen = function() {
    console.log("Connected to WebSocket Server");
};

socket.onmessage = function(event) {
    const data = JSON.parse(event.data);

    if (data.games) {
        console.log("Received updated game list:", data.games);

        if (data.total_pages) {
            currentPage = data.total_pages; 
            setupPagination(data.total_pages, currentPage);
        }
        updateGameTable(data.games);
    }
};

let reconnectAttempts = 0;
const maxReconnectAttempts = 3;

socket.onclose = function() {
    console.log("Disconnected from WebSocket server, attempting to reconnect...");
    
    if (reconnectAttempts < maxReconnectAttempts) {
        reconnectAttempts++;
        setTimeout(() => {
            window.location.reload();
        }, 5000);
    } else {
        console.error("Max reconnect attempts reached. Please check your connection.");
    }
};


function updateGameTable(newGames, currentPage) {
    const tableBody = document.querySelector('#game-list-table tbody');
    const pageIndicator = document.getElementById('pagination');

    if (currentPage > 1) {
        newGames.forEach(game => {
            const existingRow = document.querySelector(`#game-${game.id}`);
            if (!existingRow) {
                const row = document.createElement('tr');
                row.id = `game-${game.id}`;
                row.innerHTML = `
                    <td>${game.white_player || 'Unknown'}</td>
                    <td>${game.white_elo || 'N/A'}</td>
                    <td>${game.black_player || 'Unknown'}</td>
                    <td>${game.black_elo || 'N/A'}</td>
                    <td>${game.result || 'N/A'}</td>
                    <td>${game.date || 'N/A'}</td>
                    <td>${game.site || 'N/A'}</td>
                `;
                tableBody.appendChild(row);
            }
        });

        pageIndicator.innerHTML = `Page: ${currentPage}`;
    }
}

function getCsrfToken() {
    let csrfToken = document.cookie.match(/csrftoken=([^;]*)/);
    return csrfToken ? csrfToken[1] : '';
}

document.getElementById('pgn-file').addEventListener('change', async function(event) {
    let file = event.target.files[0];
    if (!file) {
        alert("Please select a PGN file.");
        return;
    }

    let fileName = file.name.toLowerCase();
    if (!fileName.endsWith('.pgn')) {
        alert("Only PGN files (.pgn) are allowed!");
        document.getElementById('pgn-file').value = ''; 
        return;
    }

    let formData = new FormData();
    formData.append('pgn_file', file);

    function getCsrfToken() {
        let csrfToken = document.cookie.match(/csrftoken=([^;]*)/);
        return csrfToken ? csrfToken[1] : '';
    }

    try {
        let uploadUrl = document.getElementById('pgn-file').dataset.uploadUrl;
        let response = await fetch(uploadUrl, {
            method: 'POST',
            body: formData,
            headers: {
                'X-CSRFToken': getCsrfToken()  // Dodavanje CSRF tokena u zahtjev
            }
        });

        let result = await response.json();
        if (result.success) {
            alert("PGN file successfully uploaded!");
            location.reload();
        } else {
            alert("Error uploading PGN file: " + result.error);
        }
    } catch (error) {
        console.error("Upload failed", error);
        alert("An error occurred while uploading.");
    }
});


