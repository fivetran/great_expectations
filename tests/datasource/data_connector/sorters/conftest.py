import pytest


@pytest.fixture
def periodic_table_of_elements():
    # fmt: off
    data = [
        "Hydrogen", "Helium", "Lithium", "Beryllium", "Boron", "Carbon", "Nitrogen", "Oxygen", "Fluorine", "Neon",  # noqa: E501 # FIXME CoP
        "Sodium", "Magnesium", "Aluminum", "Silicon", "Phosphorus", "Sulfur", "Chlorine", "Argon", "Potassium", "Calcium",  # noqa: E501 # FIXME CoP
        "Scandium", "Titanium", "Vanadium", "Chromium", "Manganese", "Iron", "Cobalt", "Nickel", "Copper", "Zinc",  # noqa: E501 # FIXME CoP
        "Gallium", "Germanium", "Arsenic", "Selenium", "Bromine", "Krypton", "Rubidium", "Strontium", "Yttrium", "Zirconium",  # noqa: E501 # FIXME CoP
        "Niobium", "Molybdenum", "Technetium", "Ruthenium", "Rhodium", "Palladium", "Silver", "Cadmium", "Indium", "Tin",  # noqa: E501 # FIXME CoP
        "Antimony", "Tellurium", "Iodine", "Xenon", "Cesium", "Barium", "Lanthanum", "Cerium", "Praseodymium", "Neodymium",  # noqa: E501 # FIXME CoP
        "Promethium", "Samarium", "Europium", "Gadolinium", "Terbium", "Dysprosium", "Holmium", "Erbium", "Thulium", "Ytterbium",  # noqa: E501 # FIXME CoP
        "Lutetium", "Hafnium", "Tantalum", "Tungsten", "Rhenium", "Osmium", "Iridium", "Platinum", "Gold", "Mercury",  # noqa: E501 # FIXME CoP
        "Thallium", "Lead", "Bismuth", "Polonium", "Astatine", "Radon", "Francium", "Radium", "Actinium", "Thorium",  # noqa: E501 # FIXME CoP
        "Protactinium", "Uranium", "Neptunium", "Plutonium", "Americium", "Curium", "Berkelium", "Californium", "Einsteinium", "Fermium",  # noqa: E501 # FIXME CoP
        "Mendelevium", "Nobelium", "Lawrencium", "Rutherfordium", "Dubnium", "Seaborgium", "Bohrium", "Hassium", "Meitnerium", "Darmstadtium",  # noqa: E501 # FIXME CoP
        "Roentgenium", "Copernicium", "Nihomium", "Flerovium", "Moscovium", "Livermorium", "Tennessine", "Oganesson",  # noqa: E501 # FIXME CoP
    ]
    # fmt: on
    return data
