from mydemands.self_tests import run_crypto_self_test


def test_self_test_crypto_logic():
    assert run_crypto_self_test() == 0
