#!/usr/bin/env python3

import os
import sys

def make_word_index(directory):
    word_locations = {}
    for dir_path, _, files in os.walk(directory):
        for filename in files:
            filepath = os.path.join(dir_path, filename)
            try:
                with open(filepath, 'r', errors='ignore') as file:  
                    for line_num, line in enumerate(file, 1):
                        clean_line = ""
                        for char in line.lower():
                            if char.isalnum():
                                clean_line += char
                            else:
                                clean_line += " "
                        words = clean_line.split()
                        for word in words:
                            if word not in word_locations:
                                word_locations[word] = []
                            word_locations[word].append({
                                'filepath': filepath,
                                'line_num': line_num,
                                'line': line.strip()
                            })
            except Exception as e:
                print(f"Error processing file {filepath}: {e}")
                continue
    return word_locations

def parse_query(query):
    parts = query.split()
    required_words = []
    optional_words = []
    or_groups = []

    i = 0
    while i < len(parts):
        part = parts[i]

        if part.startswith("+("):  # start of an OR group
            or_group = []
            part = part[2:]  # remove '+('
            if part.endswith(")"):  # single word OR group
                or_group.append(part[:-1].lower())
            else:
                while i < len(parts):
                    if part.endswith(")"):  # end of OR group
                        or_group.append(part[:-1].lower())
                        break
                    else:
                        or_group.append(part.lower())
                        i += 1
                        part = parts[i]
            or_groups.append(or_group)
        elif part.startswith("+"):  # required word
            required_words.append(part[1:].lower())
        else:  # optional word
            optional_words.append(part.lower())

        i += 1

    return required_words, optional_words, or_groups

def search(index, query):
    required, optional, or_groups = parse_query(query)

    matches = []

    # find locations for required words
    required_locations = None
    for word in required:
        word_locs = set()
        if word in index:
            for loc in index[word]:
                word_locs.add((loc['filepath'], loc['line_num']))
        if required_locations is None:
            required_locations = word_locs
        else:
            required_locations &= word_locs

    # Handle OR groups
    for group in or_groups:
        group_locations = set()
        for word in group:
            if word in index:
                for loc in index[word]:
                    group_locations.add((loc['filepath'], loc['line_num']))
        if required_locations is None:
            required_locations = group_locations
        else:
            required_locations &= group_locations

    # if no required words, use optional words
    if required_locations is None:
        required_locations = set()
        for word in optional:
            if word in index:
                for loc in index[word]:
                    required_locations.add((loc['filepath'], loc['line_num']))

    # process matches
    if required_locations:
        for filepath, line_num in required_locations:
            line = None
            for loc in index.get(word, []):
                if loc['filepath'] == filepath and loc['line_num'] == line_num:
                    line = loc['line']
                    break
            if line:
                score = 0
                for word in optional:
                    if word in line.lower():
                        score += 1
                matches.append((filepath, line_num, line, score))

    # sort matches by score
    matches.sort(key=lambda x: x[3], reverse=True)
    return matches

def main():
    if len(sys.argv) != 3 or sys.argv[1] != '--dir':
        print("Usage: python search.py --dir <directory>")
        return

    print("Building search index...")
    index = make_word_index(sys.argv[2])
    print("Ready for searches!")

    while True:
        try:
            query = input("> ")
            if query.lower() == 'quit':
                break
            results = search(index, query)
            if not results:
                print("No matches found")
            else:
                for filepath, line_num, line, _ in results:
                    print(f"{filepath} {line_num} \"{line}\"")
        except KeyboardInterrupt:
            break
        except Exception as e:
            print(f"Error: {e}")

if __name__ == "__main__":
    main()
