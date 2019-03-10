from tomate.core.constant import Base


def test_get_task_by_index():
    class Dummy(Base):
        a = 1
        b = 2

    assert Dummy.a == Dummy.by_index(0)
    assert Dummy.b == Dummy.by_index(1)
