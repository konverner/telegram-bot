from telegram_bot.src.telegram_bot.api import bot


def test_send_welcome(mocker):
    # Arrange
    mock_bot = mocker.MagicMock()
    mock_app = mocker.MagicMock()
    mocker.patch.object(bot, "bot", return_value=mock_bot)
    mocker.patch.object(bot, "app", return_value=mock_app)
    mock_message = mocker.MagicMock()
    mock_message.text = "test message"
    mock_message.chat.id = 12345
    mock_app.run.return_value = "test response"

    # Act
    bot.send_welcome(mock_message)

    # Assert
    mock_app.run.assert_called_once_with("test message")
    mock_bot.reply_to.assert_called_once_with(mock_message, "test response")
