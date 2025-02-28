CXX = g++
CXXFLAGS = -O3 -march=native -mtune=native -flto -std=c++20 -Wall -Ialglib-cpp/src
SRC = main.cpp $(wildcard alglib-cpp/src/*.cpp)
OBJ = $(SRC:.cpp=.o)
TARGET = main

all: $(TARGET)

$(TARGET): $(OBJ)
	$(CXX) $(OBJ) -o $(TARGET)

%.o: %.cpp
	$(CXX) $(CXXFLAGS) -c $< -o $@

clean:
	rm -f $(OBJ) $(TARGET)
