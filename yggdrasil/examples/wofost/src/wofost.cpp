#include <iostream>
// Include methods for input/output channels
#include "YggInterface.hpp"

int main(int argc, char *argv[]) {
  // Initialize input/output channels
  YggJSONObjectInput in_channel("input");
  YggJSONObjectOutput out_channel("output");

  // Declare resulting variables and create buffer for received message
  int flag = 1;
  rapidjson::Document obj;
  rapidjson::CrtAllocator allocator;
  double* amaxtb_x = NULL;
  double* amaxtb_y = NULL;
  char** keys = NULL;
  size_t nkeys, i;
  double co2;
  rapidjson::SizeType n_amaxtb;

  // Loop until there is no longer input or the queues are closed
  while (flag >= 0) {
  
    // Receive input from input channel
    // If there is an error, the flag will be negative
    // Otherwise, it is the size of the received message
    flag = in_channel.recv(1, &obj);
    if (flag < 0) {
      std::cout << "C++ Model: No more input." << std::endl;
      break;
    }

    // Print received message
    std::cout << "C++ Model:" << std::endl <<
      document2string(obj) << std::endl;

    // Get double precision floating point element
    co2 = obj["CO2"].GetDouble();
    std::cout << "C++ Model: CO2 = " << co2 << std::endl;

    // Get array element
    const rapidjson::Value& amaxtb = obj["AMAXTB"];
    amaxtb[0].Get1DArray(amaxtb_x, n_amaxtb, obj.GetAllocator());
    amaxtb[1].Get1DArray(amaxtb_y, n_amaxtb, obj.GetAllocator());
    std::cout << "C++ Model: AMAXTB = " << std::endl;
    for (i = 0; i < n_amaxtb; i++) {
      std::cout << "\t" << amaxtb_x[i] << "\t" << amaxtb_y[i] << std::endl;
    }

    // Send output to output channel
    // If there is an error, the flag will be negative
    flag = out_channel.send(1, &obj);
    if (flag < 0) {
      std::cout << "C++ Model: Error sending output." << std::endl;
      break;
    }

  }

  return 0;
}

