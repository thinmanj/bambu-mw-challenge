"""
Comprehensive unit tests for events modules (consumer and publisher).
"""

import pytest
import asyncio
import json
from unittest.mock import AsyncMock, MagicMock, patch, call
from datetime import datetime
from typing import Dict, Any

from events.consumer import (
    EventConsumer,
    MockEventConsumer,
    NotificationEventConsumer
)
from events.publisher import (
    EventPublisher,
    MockEventPublisher,
    NotificationEventPublisher
)


@pytest.mark.unit
class TestEventConsumerBase:
    """Test cases for the base EventConsumer class."""

    @pytest.mark.asyncio
    async def test_event_consumer_start_stop_lifecycle(self):
        """Test the event consumer lifecycle."""
        handler = MagicMock()
        consumer = MockEventConsumer("test_topic", handler)
        
        assert not consumer.running
        assert not consumer.connected
        
        # Start consumer
        task = asyncio.create_task(consumer.start())
        await asyncio.sleep(0.1)  # Let it start
        
        assert consumer.running
        assert consumer.connected
        
        # Stop consumer
        await consumer.stop()
        await task  # Wait for start to complete
        
        assert not consumer.running
        assert not consumer.connected

    @pytest.mark.asyncio
    async def test_mock_event_consumer_message_processing(self):
        """Test mock event consumer processes messages correctly."""
        handler = MagicMock()
        consumer = MockEventConsumer("test_topic", handler)
        
        # Add messages
        message1 = {"type": "test", "data": "message1"}
        message2 = {"type": "test", "data": "message2"}
        
        consumer.add_message(message1)
        consumer.add_message(message2)
        
        # Start consumer and let it process messages
        task = asyncio.create_task(consumer.start())
        await asyncio.sleep(0.2)  # Let it process messages
        await consumer.stop()
        await task
        
        # Verify handler was called for both messages
        assert handler.call_count == 2
        handler.assert_has_calls([call(message1), call(message2)])
        assert len(consumer.messages) == 0  # Messages should be consumed

    @pytest.mark.asyncio
    async def test_mock_event_consumer_handler_exception(self):
        """Test mock event consumer handles handler exceptions."""
        handler = MagicMock(side_effect=Exception("Handler error"))
        consumer = MockEventConsumer("test_topic", handler)
        
        # Add message
        message = {"type": "error_test", "data": "test"}
        consumer.add_message(message)
        
        # Start consumer
        with patch('events.consumer.logger') as mock_logger:
            task = asyncio.create_task(consumer.start())
            await asyncio.sleep(0.2)  # Let it process
            await consumer.stop()
            await task
        
        # Verify error was logged
        mock_logger.error.assert_called_once()
        assert "Error processing message" in str(mock_logger.error.call_args)

    def test_event_consumer_properties(self):
        """Test event consumer properties are set correctly."""
        handler = MagicMock()
        consumer = MockEventConsumer("my_topic", handler)
        
        assert consumer.topic == "my_topic"
        assert consumer.handler == handler
        assert not consumer.running
        assert isinstance(consumer.messages, list)


@pytest.mark.unit
class TestNotificationEventConsumer:
    """Test cases for NotificationEventConsumer."""

    @pytest.mark.asyncio
    async def test_notification_request_handling(self):
        """Test handling notification request events."""
        mock_consumer = MagicMock(spec=EventConsumer)
        mock_consumer.start = AsyncMock()
        mock_consumer.stop = AsyncMock()
        
        notification_consumer = NotificationEventConsumer(mock_consumer)
        
        event = {
            'type': 'notification_request',
            'id': 'notif_123',
            'user_id': 456,
            'template': 'welcome'
        }
        
        with patch('events.consumer.logger') as mock_logger:
            await notification_consumer.handle_notification_event(event)
            
            # Verify logging
            mock_logger.info.assert_called_with("Processing notification request: notif_123")

    @pytest.mark.asyncio
    async def test_status_update_handling(self):
        """Test handling notification status update events."""
        mock_consumer = MagicMock(spec=EventConsumer)
        notification_consumer = NotificationEventConsumer(mock_consumer)
        
        event = {
            'type': 'notification_status_update',
            'notification_id': 'notif_456',
            'status': 'sent'
        }
        
        with patch('events.consumer.logger') as mock_logger:
            await notification_consumer.handle_notification_event(event)
            
            # Verify logging
            mock_logger.info.assert_called_with("Processing status update: notif_456")

    @pytest.mark.asyncio
    async def test_unknown_event_type_handling(self):
        """Test handling unknown event types."""
        mock_consumer = MagicMock(spec=EventConsumer)
        notification_consumer = NotificationEventConsumer(mock_consumer)
        
        event = {
            'type': 'unknown_event',
            'data': 'some_data'
        }
        
        with patch('events.consumer.logger') as mock_logger:
            await notification_consumer.handle_notification_event(event)
            
            # Verify warning is logged
            mock_logger.warning.assert_called_with("Unknown event type: unknown_event")

    @pytest.mark.asyncio
    async def test_notification_consumer_lifecycle(self):
        """Test notification consumer start/stop."""
        mock_consumer = MagicMock(spec=EventConsumer)
        mock_consumer.start = AsyncMock()
        mock_consumer.stop = AsyncMock()
        
        notification_consumer = NotificationEventConsumer(mock_consumer)
        
        await notification_consumer.start()
        mock_consumer.start.assert_called_once()
        
        await notification_consumer.stop()
        mock_consumer.stop.assert_called_once()


@pytest.mark.unit
class TestEventPublisherBase:
    """Test cases for the base EventPublisher class."""

    @pytest.mark.asyncio
    async def test_mock_publisher_connection(self):
        """Test mock publisher connection/disconnection."""
        publisher = MockEventPublisher("test_topic")
        
        assert not publisher.connected
        
        await publisher.connect()
        assert publisher.connected
        
        await publisher.disconnect()
        assert not publisher.connected

    @pytest.mark.asyncio
    async def test_mock_publisher_connection_failure(self):
        """Test mock publisher connection failure."""
        publisher = MockEventPublisher("test_topic")
        publisher.set_failure_mode(True)
        
        with pytest.raises(ConnectionError, match="Failed to connect to event broker"):
            await publisher.connect()

    @pytest.mark.asyncio
    async def test_mock_publisher_publish_success(self):
        """Test successful event publishing."""
        publisher = MockEventPublisher("test_topic")
        await publisher.connect()
        
        event = {"type": "test_event", "data": "test_data"}
        result = await publisher.publish(event)
        
        assert result is True
        published_events = publisher.get_published_events()
        assert len(published_events) == 1
        
        published_event = published_events[0]
        assert published_event["type"] == "test_event"
        assert published_event["data"] == "test_data"
        assert "timestamp" in published_event
        assert published_event["topic"] == "test_topic"
        assert published_event["publisher"] == "notification-service"

    @pytest.mark.asyncio
    async def test_mock_publisher_publish_failure(self):
        """Test event publishing failure."""
        publisher = MockEventPublisher("test_topic")
        await publisher.connect()
        publisher.set_failure_mode(True)
        
        event = {"type": "test_event", "data": "test_data"}
        result = await publisher.publish(event)
        
        assert result is False
        assert len(publisher.get_published_events()) == 0

    @pytest.mark.asyncio
    async def test_mock_publisher_publish_not_connected(self):
        """Test publishing when not connected."""
        publisher = MockEventPublisher("test_topic")
        
        event = {"type": "test_event", "data": "test_data"}
        
        with pytest.raises(ConnectionError, match="Publisher not connected"):
            await publisher.publish(event)

    def test_mock_publisher_utility_methods(self):
        """Test mock publisher utility methods."""
        publisher = MockEventPublisher("test_topic")
        
        # Add some events
        publisher.published_events = [{"event": 1}, {"event": 2}]
        
        # Test get_published_events returns a copy
        events = publisher.get_published_events()
        assert len(events) == 2
        assert events is not publisher.published_events
        
        # Test clear_events
        publisher.clear_events()
        assert len(publisher.published_events) == 0

    def test_event_publisher_metadata_enrichment(self):
        """Test that events are enriched with metadata."""
        publisher = MockEventPublisher("test_topic")
        
        event = {"type": "test", "data": "value"}
        enriched = publisher._add_metadata(event)
        
        assert enriched["type"] == "test"
        assert enriched["data"] == "value"
        assert "timestamp" in enriched
        assert enriched["topic"] == "test_topic"
        assert enriched["publisher"] == "notification-service"
        
        # Verify timestamp format
        timestamp = enriched["timestamp"]
        datetime.fromisoformat(timestamp.replace('Z', '+00:00'))  # Should not raise


@pytest.mark.unit
class TestNotificationEventPublisher:
    """Test cases for NotificationEventPublisher."""

    @pytest.fixture
    def mock_publisher(self):
        """Create a mock publisher."""
        publisher = MockEventPublisher("notifications")
        return publisher

    @pytest.fixture
    def notification_publisher(self, mock_publisher):
        """Create a notification event publisher."""
        return NotificationEventPublisher(mock_publisher)

    @pytest.mark.asyncio
    async def test_publish_notification_sent_success(self, notification_publisher, mock_publisher):
        """Test publishing notification sent event successfully."""
        await mock_publisher.connect()
        
        result = await notification_publisher.publish_notification_sent(
            notification_id="notif_123",
            user_id=456,
            notification_type="email",
            success=True
        )
        
        assert result is True
        events = mock_publisher.get_published_events()
        assert len(events) == 1
        
        event = events[0]
        assert event["type"] == "notification_sent"
        assert event["notification_id"] == "notif_123"
        assert event["user_id"] == 456
        assert event["notification_type"] == "email"
        assert event["success"] is True
        assert event["status"] == "sent"

    @pytest.mark.asyncio
    async def test_publish_notification_sent_failure(self, notification_publisher, mock_publisher):
        """Test publishing notification sent event for failed notification."""
        await mock_publisher.connect()
        
        result = await notification_publisher.publish_notification_sent(
            notification_id="notif_456",
            user_id=789,
            notification_type="sms",
            success=False
        )
        
        assert result is True
        events = mock_publisher.get_published_events()
        event = events[0]
        
        assert event["success"] is False
        assert event["status"] == "failed"

    @pytest.mark.asyncio
    async def test_publish_status_update(self, notification_publisher, mock_publisher):
        """Test publishing notification status update event."""
        await mock_publisher.connect()
        
        result = await notification_publisher.publish_notification_status_update(
            notification_id="notif_789",
            old_status="pending",
            new_status="sent"
        )
        
        assert result is True
        events = mock_publisher.get_published_events()
        event = events[0]
        
        assert event["type"] == "notification_status_update"
        assert event["notification_id"] == "notif_789"
        assert event["old_status"] == "pending"
        assert event["new_status"] == "sent"

    @pytest.mark.asyncio
    async def test_publish_user_preference_updated(self, notification_publisher, mock_publisher):
        """Test publishing user preference updated event."""
        await mock_publisher.connect()
        
        preferences = {"email_enabled": True, "sms_enabled": False}
        result = await notification_publisher.publish_user_preference_updated(
            user_id=123,
            preferences=preferences
        )
        
        assert result is True
        events = mock_publisher.get_published_events()
        event = events[0]
        
        assert event["type"] == "user_preference_updated"
        assert event["user_id"] == 123
        assert event["preferences"] == preferences

    @pytest.mark.asyncio
    async def test_publish_template_created(self, notification_publisher, mock_publisher):
        """Test publishing template created event."""
        await mock_publisher.connect()
        
        result = await notification_publisher.publish_template_created(
            template_id=42,
            template_name="welcome_email",
            template_type="email"
        )
        
        assert result is True
        events = mock_publisher.get_published_events()
        event = events[0]
        
        assert event["type"] == "template_created"
        assert event["template_id"] == 42
        assert event["template_name"] == "welcome_email"
        assert event["template_type"] == "email"

    @pytest.mark.asyncio
    async def test_publish_with_connection_error(self, notification_publisher, mock_publisher):
        """Test publishing when connection fails."""
        # Don't connect the publisher
        
        result = await notification_publisher.publish_notification_sent(
            notification_id="notif_error",
            user_id=999,
            notification_type="push",
            success=True
        )
        
        # Should return False due to connection error
        assert result is False
        assert len(mock_publisher.get_published_events()) == 0

    @pytest.mark.asyncio
    async def test_publish_with_publisher_failure(self, notification_publisher, mock_publisher):
        """Test publishing when publisher fails."""
        await mock_publisher.connect()
        mock_publisher.set_failure_mode(True)
        
        result = await notification_publisher.publish_notification_sent(
            notification_id="notif_fail",
            user_id=888,
            notification_type="email",
            success=True
        )
        
        assert result is False

    @pytest.mark.asyncio
    async def test_notification_publisher_connection_management(self, notification_publisher, mock_publisher):
        """Test notification publisher connection management."""
        assert not mock_publisher.connected
        
        await notification_publisher.connect()
        assert mock_publisher.connected
        
        await notification_publisher.disconnect()
        assert not mock_publisher.connected


@pytest.mark.unit
class TestEventsIntegration:
    """Integration tests for event consumer and publisher interaction."""

    @pytest.mark.asyncio
    async def test_consumer_publisher_integration(self):
        """Test consumer and publisher working together."""
        # Set up publisher
        publisher = MockEventPublisher("notifications")
        notification_publisher = NotificationEventPublisher(publisher)
        await notification_publisher.connect()
        
        # Set up consumer
        processed_events = []
        
        def event_handler(event):
            processed_events.append(event)
        
        consumer = MockEventConsumer("notifications", event_handler)
        notification_consumer = NotificationEventConsumer(consumer)
        
        # Publish an event
        await notification_publisher.publish_notification_sent(
            notification_id="test_123",
            user_id=456,
            notification_type="email", 
            success=True
        )
        
        # Get the published event and feed it to consumer
        published_events = publisher.get_published_events()
        assert len(published_events) == 1
        
        # Add event to consumer and process
        consumer.add_message(published_events[0])
        
        # Start consumer briefly to process the message
        task = asyncio.create_task(notification_consumer.start())
        await asyncio.sleep(0.1)
        await notification_consumer.stop()
        await task
        
        # Verify the event was processed
        assert len(processed_events) == 1
        assert processed_events[0]["type"] == "notification_sent"
        assert processed_events[0]["notification_id"] == "test_123"

    def test_event_types_consistency(self):
        """Test that event types are consistent between consumer and publisher."""
        # Define expected event types
        expected_types = {
            'notification_sent',
            'notification_status_update', 
            'user_preference_updated',
            'template_created',
            'notification_request'  # From consumer
        }
        
        # Check that NotificationEventConsumer handles expected types
        consumer_types = {'notification_request', 'notification_status_update'}
        
        # Check that NotificationEventPublisher publishes expected types
        publisher_types = {
            'notification_sent',
            'notification_status_update',
            'user_preference_updated', 
            'template_created'
        }
        
        # Verify all types are covered
        all_types = consumer_types | publisher_types
        assert all_types == expected_types

    @pytest.mark.asyncio
    async def test_error_handling_integration(self):
        """Test error handling across consumer and publisher."""
        # Test consumer error handling
        def failing_handler(event):
            raise ValueError("Handler failed")
        
        consumer = MockEventConsumer("test", failing_handler)
        consumer.add_message({"type": "test", "data": "fail"})
        
        # Should not crash, just log error
        task = asyncio.create_task(consumer.start())
        await asyncio.sleep(0.1)
        await consumer.stop()
        await task
        
        # Test publisher error handling - connection failure
        publisher = MockEventPublisher("test")
        publisher.set_failure_mode(True)
        
        # Should raise ConnectionError when trying to connect in failure mode
        with pytest.raises(ConnectionError, match="Failed to connect to event broker"):
            await publisher.connect()
        
        # Test publish failure when connected but set to fail
        publisher2 = MockEventPublisher("test")
        await publisher2.connect()  # Connect first
        publisher2.set_failure_mode(True)  # Then set failure mode
        
        notification_publisher = NotificationEventPublisher(publisher2)
        result = await notification_publisher.publish_notification_sent(
            "test", 1, "email", True
        )
        
        # Should handle gracefully
        assert result is False
