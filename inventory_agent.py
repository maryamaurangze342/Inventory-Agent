import json
import os
import sys
from typing import Dict, Any

# -----------------------------
# Simple local inventory store
# -----------------------------
INVENTORY_FILE = "inventory_data.json"

def load_inventory() -> Dict[str, Dict[str, Any]]:
    if os.path.exists(INVENTORY_FILE):
        with open(INVENTORY_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}

def save_inventory(inventory: Dict[str, Dict[str, Any]]):
    with open(INVENTORY_FILE, "w", encoding="utf-8") as f:
        json.dump(inventory, f, indent=2, ensure_ascii=False)

# Inventory operations
def add_item(inventory, name: str, qty: int, price: float = 0.0):
    key = name.lower()
    if key in inventory:
        inventory[key]["quantity"] += qty
    else:
        inventory[key] = {"name": name, "quantity": qty, "price": price}
    save_inventory(inventory)
    return f"Added {qty} x {name}. New qty: {inventory[key]['quantity']}"

def remove_item(inventory, name: str, qty: int):
    key = name.lower()
    if key not in inventory:
        return f"Item '{name}' not found in inventory."
    if qty >= inventory[key]["quantity"]:
        inventory.pop(key)
        save_inventory(inventory)
        return f"Removed item '{name}' completely (requested {qty})."
    inventory[key]["quantity"] -= qty
    save_inventory(inventory)
    return f"Removed {qty} x {name}. Remaining qty: {inventory[key]['quantity']}"

def check_stock(inventory, name: str):
    key = name.lower()
    if key not in inventory:
        return f"Item '{name}' not found."
    it = inventory[key]
    return f"{it['name']}: quantity={it['quantity']}, price={it.get('price', 0.0)}"

def list_items(inventory):
    if not inventory:
        return "Inventory is empty."
    lines = [f"{v['name']} — qty: {v['quantity']} — price: {v.get('price',0.0)}" for v in inventory.values()]
    return "\n".join(lines)

# -----------------------------
# Attempt to build an agent using the OpenAI Agents SDK
# -----------------------------
def run_with_sdk():
    try:
        from openai.agents import Agent, Tool   # ✅ correct import
    except Exception as e:
        print("OpenAI Agents SDK not available or import failed:", e)
        print("Falling back to local CLI mode.\n")
        run_local_cli()
        return

    inventory = load_inventory()

    def sdk_add_item(params: Dict[str, Any]):
        return add_item(inventory, params.get("name"), int(params.get("quantity", 0)), float(params.get("price", 0.0)))

    def sdk_remove_item(params: Dict[str, Any]):
        return remove_item(inventory, params.get("name"), int(params.get("quantity", 0)))

    def sdk_check_stock(params: Dict[str, Any]):
        return check_stock(inventory, params.get("name"))

    def sdk_list_items(params: Dict[str, Any]):
        return list_items(inventory)

    tools = [
        Tool(name="add_item", func=sdk_add_item, description="Add quantity of an item. params: {name, quantity, price}"),
        Tool(name="remove_item", func=sdk_remove_item, description="Remove quantity or delete item. params: {name, quantity}"),
        Tool(name="check_stock", func=sdk_check_stock, description="Return stock for an item. params: {name}"),
        Tool(name="list_items", func=sdk_list_items, description="List all items in inventory"),
    ]

    agent = Agent(
        name="Inventory Manager",
        instructions="You are an Inventory Manager agent. Use the provided tools to manage inventory.",
        tools=tools,
    )

    print("Inventory Agent (SDK mode) ready. Type a request (e.g. 'add 5 apples')\nType 'exit' to quit.")

    while True:
        user = input("You: ")
        if not user:
            continue
        if user.strip().lower() in ("exit", "quit"):
            print("Goodbye.")
            break
        try:
            response = agent.run(user)
            print("Agent:", response)
        except Exception as e:
            print("Agent runtime error:", e)
            handle_local_text_command(load_inventory(), user)

# -----------------------------
# Local CLI fallback (no SDK)
# -----------------------------
def handle_local_text_command(inventory, text: str):
    t = text.lower().strip()
    parts = t.split()
    if parts[0] in ("add", "insert") and len(parts) >= 3:
        try:
            qty = int(parts[1])
            name = " ".join(parts[2:])
            print(add_item(inventory, name, qty))
        except ValueError:
            print("Can't parse quantity. Usage: add <qty> <item name>")
    elif parts[0] in ("remove", "delete") and len(parts) >= 3:
        try:
            qty = int(parts[1])
            name = " ".join(parts[2:])
            print(remove_item(inventory, name, qty))
        except ValueError:
            print("Can't parse quantity. Usage: remove <qty> <item name>")
    elif parts[0] in ("check", "stock") and len(parts) >= 2:
        name = " ".join(parts[1:])
        print(check_stock(inventory, name))
    elif parts[0] in ("list", "show"):
        print(list_items(inventory))
    else:
        print("I didn't understand. Try: add, remove, check, list")

def run_local_cli():
    inventory = load_inventory()
    print("Inventory CLI ready. Commands: add <qty> <name>, remove <qty> <name>, check <name>, list, exit")
    while True:
        try:
            cmd = input("> ")
        except (KeyboardInterrupt, EOFError):
            print("\nExiting.")
            break
        if not cmd:
            continue
        if cmd.strip().lower() in ("exit", "quit"):
            print("Goodbye.")
            break
        handle_local_text_command(inventory, cmd)

if __name__ == "__main__":
    if "--local" in sys.argv:
        run_local_cli()
    else:
        run_with_sdk()
