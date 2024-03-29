import numpy as np

from deepsudoku.utils import sudoku_utils


def count_invalid_moves(new_board, solved):
    return np.sum(
        np.logical_and(new_board != 0, np.not_equal(new_board, solved))
    )


def count_valid_moves(board, new_board, solved):
    return np.sum(
        np.logical_and.reduce(
            (board == 0, new_board != 0, np.equal(new_board, solved))
        )
    )


def test_random_moves():
    sudokus, _ = sudoku_utils.load_latest_sudoku_list()

    rng = np.random.default_rng(1)

    for n_invalid_moves in range(20):
        for n_valid_moves in range(20):
            board_index = rng.choice(range(len(sudokus)))
            board, solved = sudokus[board_index]

            new_board = sudoku_utils.make_random_moves(
                board, solved, n_valid_moves, n_invalid_moves
            )
            assert count_invalid_moves(new_board, solved) == n_invalid_moves
            assert count_valid_moves(board, new_board, solved) == n_valid_moves


def test_augmentation():
    sudokus, _ = sudoku_utils.load_latest_sudoku_list()
    rng = np.random.default_rng(1)

    for _ in range(20):
        board_index = rng.choice(range(len(sudokus)))
        _, solved = sudokus[board_index]
        solved_array = np.array([solved])
        augmented_solved_array = sudoku_utils.augment_sudokus(
            solved_array, rng
        )
        assert sudoku_utils.validate_sudoku(augmented_solved_array[0])
