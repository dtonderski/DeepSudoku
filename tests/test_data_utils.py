import numpy as np

from deepsudoku.utils import data_utils, sudoku_utils


def categorical_test(board: np.ndarray):
    board_cat = data_utils.to_categorical(board)
    for i in range(9):
        for j in range(9):
            for k in range(9):
                if board_cat[i, j, k] == 1:
                    assert board[j, k] == i + 1


def test_to_categorical():
    sudokus, _ = sudoku_utils.load_latest_sudoku_list()
    rng = np.random.default_rng(1)
    for _ in range(20):
        board_index = rng.choice(range(len(sudokus)))
        board, solved = sudokus[board_index]

        categorical_test(board)
        categorical_test(solved)


def test_to_numerical():
    sudokus, _ = sudoku_utils.load_latest_sudoku_list()
    rng = np.random.default_rng(2)
    for _ in range(20):
        board_index = rng.choice(range(len(sudokus)))
        board, solved = sudokus[board_index]

        assert np.all(
            np.equal(
                board,
                data_utils.to_numerical(data_utils.to_categorical(board)),
            )
        )
        assert np.all(
            np.equal(
                solved,
                data_utils.to_numerical(data_utils.to_categorical(solved)),
            )
        )
