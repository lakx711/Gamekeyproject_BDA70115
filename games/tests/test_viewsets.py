from games.viewsets import GameViewSet, PublisherViewSet


def test_game_viewset_serializer():
    assert GameViewSet.serializer_class is not None


def test_publisher_viewset_serializer():
    assert PublisherViewSet.serializer_class is not None