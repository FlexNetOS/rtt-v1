#!/usr/bin/env ruby
STDIN.each_line do |line|
  next if line.strip.empty?
  puts({id:"0", result:{ok:true}, error:nil}.to_json)
end
