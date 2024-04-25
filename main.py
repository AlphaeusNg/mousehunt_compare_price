import sys
import compare_marketplace_and_discord as cu

def main():
    if len(sys.argv) < 2:
        print("Usage: python main.py <function_name> <item_name>")
        return

    function_name = sys.argv[1]
    if function_name == "get_single_item_info":
        if len(sys.argv) < 3:
            print("Usage: python main.py get_single_item_info <item_name>")
            return
        item_name = sys.argv[2]
        cu.get_single_item_info(item_name)
    elif function_name == "generate_csv":
        cu.generate_csv()
    else:
        print("Invalid function name.")

if __name__ == "__main__":
    main()