from mydemands.self_tests import run_crypto_self_test


def test_crypto_self_test_passes():
    assert run_crypto_self_test() == 0
