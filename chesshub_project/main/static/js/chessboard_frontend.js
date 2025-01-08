import { Chess } from "/static/chess.js-0.13.4/chess.js"

document.addEventListener("DOMContentLoaded", function () {
    var game = new Chess();

    var board = Chessboard("board", {
        draggable: true,
        position: "start",
        pieceTheme: "/static/chessboardjs-1.0.0/img/chesspieces/wikipedia/{piece}.png",
        onDrop: onDrop
    });

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
    menu.style.justifyContent = "center";

    const boardRect = document.getElementById("board").getBoundingClientRect();
    const squareSize = boardRect.width / 8; 
    const col = targetSquare.charCodeAt(0) - 97; 
    const row = 8 - parseInt(targetSquare[1]); 
            
    menu.style.left = `${boardRect.left + col * squareSize + squareSize / 2 - 80}px`;
    menu.style.top = `${boardRect.top + row * squareSize - 60}px`;
    
    const pieces = ["q", "r", "b", "n"]; 
    const pieceImages = {
        "w": { "q": "wQ", "r": "wR", "b": "wB", "n": "wN" },
        "b": { "q": "bQ", "r": "bR", "b": "bB", "n": "bN" }
    };

    const piece = board.position()[move.substring(0, 2)]; 
    const color = piece[0]; // 'w' ili 'b'

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
        const promotionMove = move + pieceType.toUpperCase(); // Dodaj promociju u notaciju
        sendMoveToBackend(promotionMove); // Pošalji potez backendu
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
            updateButtonStates(); // Ažuriraj stanje gumba
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
            if (data.fen) {
                board.position(data.fen);
            }
            updateButtonStates(); // Ažuriraj stanje gumba
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
    console.log("Prikazujem varijacije za izbor:", variations);

    const menu = document.createElement("div");
    menu.id = "variation-menu";
    menu.style.position = "fixed";
    menu.style.top = "50%";
    menu.style.left = "50%";
    menu.style.transform = "translate(-50%, -50%)";
    menu.style.backgroundColor = "white";
    menu.style.border = "1px solid black";
    menu.style.padding = "20px";
    menu.style.zIndex = 1000;
    menu.style.textAlign = "center";

    const list = document.createElement("ul");
    list.style.listStyle = "none";
    list.style.padding = "0";
    list.style.margin = "0";

    let currentIndex = 0;

    variations.forEach((variation, index) => {
        const listItem = document.createElement("li");
        listItem.textContent = variation;
        listItem.style.padding = "10px";
        listItem.style.marginBottom = "5px";
        listItem.style.cursor = "pointer";
        listItem.style.border = "1px solid black";
        listItem.style.backgroundColor = index === currentIndex ? "#e0e0e0" : "white";

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
        const listItems = list.querySelectorAll("li");

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
            item.style.backgroundColor = index === currentIndex ? "#e0e0e0" : "white";
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
                board.position(data.fen); // Ažuriraj ploču
            }
            if (data.pgn) {
                updatePGN(data.pgn); // Ažuriraj PGN
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