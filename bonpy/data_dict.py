from collections import UserDict
from pathlib import Path

from bonpy.data_parsers import LOADERS_DICT

# FILETSTAMP_LENGTH = 19  # length of the file timestamp
# FILETSTAMP_PARSER = "%Y-%m-%dT%H_%M_%S"  # pattern of the file timestamp
# KEY_PATTERN = "log"  # pattern in the file that identify the key string


class LazyDataDict(UserDict):
    """Dictionary that loads data on demand using a dictionary of loaders."""

    # Dictionary defining loading functions for different file types.
    # By default only extention is used to identify the loader, but
    # this can be changed by prepending name patterns to match with _
    # (e.g. DLC_h5 matches all h5 files containing DLC in the name)
    # The order of this dictionary matter! Loaders will be tried in order top to bottom,
    # so if a file matches multiple loaders, the last one will be used.

    # TODO: just changing this dictionary and the functions it implements could be a reasonable
    # way to versioning the data loading process; in the future new dictionaries could be defined
    # for new data compositions.
    loaders_dict = LOADERS_DICT

    # Unknown file types will be loaded with this function:
    loaders_dict.update({"-": lambda x, _: None})

    def __init__(self, path, timestamp_begin=None):
        self.root_path = Path(path)
        self.files_dict = self._discover_files(self.root_path)

        self.timestamp_begin = timestamp_begin

        super().__init__()

    def keys(self):
        return self.files_dict.keys()

    @staticmethod
    def _discover_files(path):
        categories_to_discover = LazyDataDict.loaders_dict.keys()

        # split over beginning of timestamp, assuming convention _YYYY...
        # as default in BonsaiRX
        SPLIT_PATTERN = "_202"

        # Loop over all categories that have a parser defined.
        # For each, make a dictionary of dictionaries
        files_dict = dict()
        for file in path.glob("*"):
            name = file.stem
            file_dict = dict(file=file, category="-")
            for category in categories_to_discover:
                extension = category.split("_")[-1]
                pattern = category.split("_")[0] if "_" in category else ""

                if file.suffix[1:] == extension and pattern in file.stem:
                    name = file.stem
                    if SPLIT_PATTERN in file.stem:
                        name = name.split(SPLIT_PATTERN)[0]

                    # If we omplement a specific loader, add to the name:
                    if "_" in category:
                        name = name + "_" + category.split("_")[0]

                    file_dict = dict(file=file, category=category)

            files_dict[name] = file_dict

        return files_dict

    def __repr__(self) -> str:
        output = ""
        line_template = "{:<25} {:<13} {:<13} {:<23} {:<13}\n"
        output += line_template.format(
            "Filename", "Extension", "Category", "Reader", "Loaded"
        )
        for filename, file_info in self.files_dict.items():
            path = file_info["file"]
            # print(path)
            category = file_info["category"]
            # print(self.loaders_dict[category].__name__)
            output += line_template.format(
                filename,
                path.suffix,
                category,
                self.loaders_dict[category].__name__
                if category in self.loaders_dict.keys()
                else "-",
                ["No", "Yes"][int(filename in self.data)],
            )

        return output
        # return f"Lazy data dict with keys: {list(self.files_dict.keys())}"

    def __str__(self) -> str:
        return self.__repr__()

    def __getitem__(self, key):
        file = self.files_dict[key]["file"]
        category = self.files_dict[key]["category"]
        if key not in self.data:
            self.data[key] = self.loaders_dict[category](file, self.timestamp_begin)

        return self.data[key]


if __name__ == "__main__":
    # df = _load_ball_log_csv(
    #    "/Users/vigji/code/bonpy/tests/assets/test_dataset/M1/20231214/162720/ball-log_2023-12-14T16_27_20.csv"
    # )
    # print(df.head())

    data_dict = LazyDataDict(
        "/Users/vigji/code/bonpy/tests/assets/test_dataset/M1/20231214/162720"
    )
    for key in data_dict.keys():
        print(key)
        data_dict[key]
