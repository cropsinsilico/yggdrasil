#define _USE_MATH_DEFINES  // Required to use M_PI with MSVC
#include <math.h>
#include <stdio.h>
#include "YggInterface.hpp"


void timestep_calc(rapidjson::units::Quantity<double>& t,
		   rapidjson::Document& state) {
#define SET_(key, val)							\
  if (!state.HasMember(key)) {						\
    state.AddMember(key,						\
		    rapidjson::Value(val),				\
		    state.GetAllocator());				\
  } else {								\
    state[key].SetScalar(val);						\
  }
  // TODO: Update timesync/OSR to convert units
  // rapidjson::units::Quantity<double> x(10.0, "g");
  // rapidjson::units::Quantity<double> y(10.0, "cm/day");
  SET_("carbonAllocation2Roots", 10.0)
  SET_("saturatedConductivity", 10.0)
}


int main(int argc, char *argv[]) {

  char* t_units = argv[2];
  rapidjson::units::Quantity<double> t_step(atof(argv[1]), t_units);
  std::cout << "Hello from C++ other_model: timestep " << t_step << std::endl;
  rapidjson::units::Quantity<double> t_start(0.0, t_units);
  rapidjson::units::Quantity<double> t_end(1.0, "days");
  rapidjson::Document state_send(rapidjson::kObjectType);
  rapidjson::Document state_recv(rapidjson::kObjectType);
  timestep_calc(t_start, state_send);
  int ret = 0;
  
  // Set up connections matching yaml
  // Timestep synchronization connection will default to 'timesync'
  YggTimesync timesync("timesync", t_units);
  dtype_t* out_dtype = create_dtype_json_object(0, NULL, NULL, true);
  YggOutput out("output", out_dtype);

  // Initialize state and synchronize with other models
  rapidjson::units::Quantity<double> t = t_start;
  ret = timesync.call(3, t.value(), &state_send, &state_recv);
  if (ret < 0) {
    std::cerr << "other_model(C++): Initial sync failed." << std::endl;
    return -1;
  }
  std::cout << "other_model(C++): t = " << t;
  for (rapidjson::Value::MemberIterator it = state_recv.MemberBegin();
       it != state_recv.MemberEnd(); it++)
    std::cout << ", " << it->name.GetString() <<
      " = " << it->value.GetDouble();
  std::cout << std::endl;

  // Send initial state to output
  rapidjson::Document msg;
  msg.CopyFrom(state_recv, msg.GetAllocator());
  msg.AddMember("time", rapidjson::Value(t).Move(), msg.GetAllocator());
  ret = out.send(1, &msg);
  if (ret < 0) {
    std::cerr << "other_model(C++): Failed to send initial output for t=" <<
      t << std::endl;
    return -1;
  }

  // Iterate until end
  while (t < t_end) {

    // Perform calculations to update the state
    t = t + t_step;
    timestep_calc(t, state_send);

    // Synchronize the state
    ret = timesync.call(3, t.value(), &state_send, &state_recv);
    if (ret < 0) {
      std::cerr << "other_model(C++): sync for t=" << t << " failed" << std::endl;
      return -1;
    }
    std::cout << "other_model(C++): t = " << t;
    for (rapidjson::Value::MemberIterator it = state_recv.MemberBegin();
	 it != state_recv.MemberEnd(); it++)
      std::cout << ", " << it->name.GetString() <<
	" = " << it->value.GetDouble();
    std::cout << std::endl;

    // Send output
    msg.CopyFrom(state_recv, msg.GetAllocator());
    msg.AddMember("time", rapidjson::Value(t).Move(), msg.GetAllocator());
    ret = out.send(1, &msg);
    if (ret < 0) {
      std::cerr << "other_model(C++): Failed to send output for t=" << t << std::endl;
      return -1;
    }
  }

  std::cout << "Goodbye from C++ other_model" << std::endl;
  return 0;
    
}
