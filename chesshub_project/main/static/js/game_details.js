import { Chess } from "/static/chess.js-0.13.4/chess.js";

document.addEventListener("DOMContentLoaded", function () {
    const board = Chessboard("board", {
        draggable: false,
        position: "start",
        pieceTheme: "/static/chessboardjs-1.0.0/img/chesspieces/wikipedia/{piece}.png",
    });

    let moves = []; // Potezi iz backenda
    let currentMoveIndex = 0;

    // Dohvat poteza iz backend-a
    fetch(`/get_game_moves/${gameId}/`)
        .then(response => response.json())
        .then(data => {
            if (data.error) {
                console.error("Error fetching game moves:", data.error);
                return;
            }
            moves = data.moves; // Postavi poteze
            updateBoardToCurrentMove(); // Postavi početnu poziciju
            updateButtonStates(); // Ažuriraj gumbe
        })
        .catch(error => console.error("Error:", error));

    function updateBoardToCurrentMove() {
        const game = new Chess();
        moves.slice(0, currentMoveIndex).forEach(move => game.move(move));
        board.position(game.fen());
    }

    function updateButtonStates() {
        document.getElementById("prev-move").disabled = currentMoveIndex === 0;
        document.getElementById("next-move").disabled = currentMoveIndex === moves.length;
    }

    document.getElementById("prev-move").addEventListener("click", function () {
        if (currentMoveIndex > 0) {
            currentMoveIndex--;
            updateBoardToCurrentMove();
            updateButtonStates();
        }
    });

    document.getElementById("next-move").addEventListener("click", function () {
        if (currentMoveIndex < moves.length) {
            currentMoveIndex++;
            updateBoardToCurrentMove();
            updateButtonStates();
        }
    });
});
