"""The number platform for Helios Easy Controls integration."""

import logging
from typing import Self

from homeassistant.components.number import (
    NumberDeviceClass,
    NumberEntity,
    NumberEntityDescription,
    NumberMode,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_MAC, UnitOfTemperature
from homeassistant.core import HomeAssistant
from homeassistant.helpers import device_registry
from homeassistant.helpers.entity import DeviceInfo, EntityCategory
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from custom_components.easycontrols import get_coordinator
from custom_components.easycontrols.const import (
    VARIABLE_BYPASS_EXTRACT_AIR_TEMPERATURE,
    VARIABLE_BYPASS_FROM_DAY,
    VARIABLE_BYPASS_FROM_MONTH,
    VARIABLE_BYPASS_OUTDOOR_AIR_TEMPERATURE,
    VARIABLE_BYPASS_TO_DAY,
    VARIABLE_BYPASS_TO_MONTH,
)
from custom_components.easycontrols.coordinator import EasyControlsDataUpdateCoordinator
from custom_components.easycontrols.modbus_variable import IntModbusVariable

_LOGGER = logging.getLogger(__name__)


class EasyControlsNumber(NumberEntity):
    """Represents a writable Helios Modbus integer variable as a number entity."""

    def __init__(
        self: Self,
        coordinator: EasyControlsDataUpdateCoordinator,
        variable: IntModbusVariable,
        description: NumberEntityDescription,
    ):
        """
        Initialize a new instance of `EasyControlsNumber` class.

        Args:
            coordinator:
                The coordinator instance.
            variable:
                The Modbus variable to read and write.
            description:
                The number entity description.

        """
        self.entity_description = description
        self._coordinator = coordinator
        self._variable = variable
        self._attr_unique_id = self._coordinator.mac + self.name
        self._attr_should_poll = False
        self._attr_mode = NumberMode.BOX
        self._attr_device_info = DeviceInfo(
            connections={(device_registry.CONNECTION_NETWORK_MAC, self._coordinator.mac)}
        )

        def update_listener(
            variable: IntModbusVariable,  # noqa: ARG001
            value: int,
        ) -> None:
            self._value_updated(value)

        self._update_listener = update_listener

    async def async_added_to_hass(self: Self) -> None:
        """
        Called when the entity is added to Home Assistant.

        It registers the update listener to the coordinator.
        """
        self._coordinator.add_listener(self._variable, self._update_listener)
        return await super().async_added_to_hass()

    async def async_will_remove_from_hass(self) -> None:
        """
        Called when the entity will be removed from Home Assistant.

        It removes the update listener from the coordinator.
        """
        self._coordinator.remove_listener(self._variable, self._update_listener)
        return await super().async_will_remove_from_hass()

    def _value_updated(self: Self, value: int) -> None:
        self._attr_native_value = value
        self._attr_available = value is not None
        self.schedule_update_ha_state(False)

    async def async_set_native_value(self: Self, value: float) -> None:
        """
        Write the new value to the variable on the Helios device.

        Args:
            value: The new value to set on the device.

        """
        await self._coordinator.set_variable(self._variable, int(value))
        self._coordinator.schedule_update(self._variable)


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """
    Setup of Helios Easy Controls number entities for the specified config_entry.

    Args:
        hass: The Home Assistant instance.
        config_entry: The config entry which is used to create the entities.
        async_add_entities: The callback which can be used to add new entities to Home Assistant.

    """
    _LOGGER.info("Setting up Helios EasyControls number entities.")

    coordinator = get_coordinator(hass, config_entry.data[CONF_MAC])

    async_add_entities(
        [
            EasyControlsNumber(
                coordinator,
                VARIABLE_BYPASS_EXTRACT_AIR_TEMPERATURE,
                NumberEntityDescription(
                    key="bypass_room_temperature",
                    name=f"{coordinator.device_name} bypass room temperature",
                    icon="mdi:thermometer-check",
                    native_unit_of_measurement=UnitOfTemperature.CELSIUS,
                    device_class=NumberDeviceClass.TEMPERATURE,
                    native_min_value=10,
                    native_max_value=40,
                    native_step=1,
                    entity_category=EntityCategory.CONFIG,
                ),
            ),
            EasyControlsNumber(
                coordinator,
                VARIABLE_BYPASS_OUTDOOR_AIR_TEMPERATURE,
                NumberEntityDescription(
                    key="bypass_min_outdoor_temperature",
                    name=f"{coordinator.device_name} bypass minimum outdoor temperature",
                    icon="mdi:thermometer-low",
                    native_unit_of_measurement=UnitOfTemperature.CELSIUS,
                    device_class=NumberDeviceClass.TEMPERATURE,
                    native_min_value=5,
                    native_max_value=20,
                    native_step=1,
                    entity_category=EntityCategory.CONFIG,
                ),
            ),
            EasyControlsNumber(
                coordinator,
                VARIABLE_BYPASS_FROM_DAY,
                NumberEntityDescription(
                    key="bypass_season_from_day",
                    name=f"{coordinator.device_name} bypass season from day",
                    icon="mdi:calendar-start",
                    native_min_value=1,
                    native_max_value=31,
                    native_step=1,
                    entity_category=EntityCategory.CONFIG,
                ),
            ),
            EasyControlsNumber(
                coordinator,
                VARIABLE_BYPASS_FROM_MONTH,
                NumberEntityDescription(
                    key="bypass_season_from_month",
                    name=f"{coordinator.device_name} bypass season from month",
                    icon="mdi:calendar-start",
                    native_min_value=1,
                    native_max_value=12,
                    native_step=1,
                    entity_category=EntityCategory.CONFIG,
                ),
            ),
            EasyControlsNumber(
                coordinator,
                VARIABLE_BYPASS_TO_DAY,
                NumberEntityDescription(
                    key="bypass_season_to_day",
                    name=f"{coordinator.device_name} bypass season to day",
                    icon="mdi:calendar-end",
                    native_min_value=1,
                    native_max_value=31,
                    native_step=1,
                    entity_category=EntityCategory.CONFIG,
                ),
            ),
            EasyControlsNumber(
                coordinator,
                VARIABLE_BYPASS_TO_MONTH,
                NumberEntityDescription(
                    key="bypass_season_to_month",
                    name=f"{coordinator.device_name} bypass season to month",
                    icon="mdi:calendar-end",
                    native_min_value=1,
                    native_max_value=12,
                    native_step=1,
                    entity_category=EntityCategory.CONFIG,
                ),
            ),
        ]
    )

    _LOGGER.info("Setting up Helios EasyControls number entities completed.")
